"""Polymarket prediction market data tool for LangChain agents.

Fetches read-only data from Polymarket's public Gamma API and returns
formatted summaries of event odds, volume, and end dates.
No API key required.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from langchain_core.tools import tool

_BASE_URL = "https://gamma-api.polymarket.com"
_USER_AGENT = "tradingagents-polymarket/1.0"


# ---------------------------------------------------------------------------
# Internal helpers (ported from polymarket-data/scripts/polymarket.py)
# ---------------------------------------------------------------------------

def _fetch_json(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    query = urllib.parse.urlencode(params or {}, doseq=True)
    url = f"{_BASE_URL}{endpoint}"
    if query:
        url = f"{url}?{query}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _maybe_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return parsed
    return []


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_probability(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return "N/A"
    return f"{number * 100:.1f}%"


def _format_money(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return "N/A"
    if number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"
    if number >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"
    if number >= 1_000:
        return f"${number / 1_000:.1f}K"
    return f"${number:.0f}"


def _first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _format_market_odds(market: dict[str, Any]) -> tuple[str, str]:
    outcomes = _maybe_json_list(market.get("outcomes"))
    prices = _maybe_json_list(market.get("outcomePrices"))

    if prices:
        labels: list[str] = []
        for idx, _ in enumerate(prices):
            if idx < len(outcomes) and outcomes[idx]:
                labels.append(str(outcomes[idx]))
            else:
                labels.append(f"Outcome {idx + 1}")
        shown = ", ".join(
            f"{label}: {_format_probability(price)}"
            for label, price in list(zip(labels, prices))[:3]
        )
    else:
        shown = "Odds unavailable"

    volume = _first_present(market, "volume", "volumeNum")
    volume_part = f" | Volume {_format_money(volume)}" if volume is not None else ""
    return shown, volume_part


def _format_market_line(market: dict[str, Any]) -> str:
    question = (
        _first_present(market, "question", "title", "groupItemTitle")
        or "Unknown market"
    )
    shown, volume_part = _format_market_odds(market)
    return f"- {question} | {shown}{volume_part}"


def _format_event_summary(event: dict[str, Any], markets_limit: int = 3) -> str:
    title = _first_present(event, "title", "question") or "Unknown event"
    slug = event.get("slug")
    url_part = f"https://polymarket.com/event/{slug}" if slug else None

    lines = [title]

    # Always show volume so the LLM can judge event significance
    volume = _first_present(event, "volume", "volume24hr")
    volume_str = _format_money(volume) if volume is not None else "N/A"
    lines.append(f"Total Volume: {volume_str}")

    end_date = event.get("endDate") or event.get("end_date_iso")
    if end_date and isinstance(end_date, str):
        lines.append(f"Ends: {end_date[:10]}")

    markets = event.get("markets") or []
    if isinstance(markets, list) and markets:
        lines.append("Top markets:")
        for market in markets[:markets_limit]:
            if isinstance(market, dict):
                lines.append(_format_market_line(market))
        remaining = len(markets) - min(len(markets), markets_limit)
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")

    if url_part:
        lines.append(f"URL: {url_part}")

    return "\n".join(lines)


def _format_market_summary(market: dict[str, Any]) -> str:
    question = _first_present(market, "question", "title") or "Unknown market"
    shown, volume_part = _format_market_odds(market)
    # Always show volume so the LLM can judge market significance
    volume = _first_present(market, "volume", "volumeNum")
    volume_str = _format_money(volume) if volume is not None else "N/A"
    lines = [question, f"Odds: {shown}", f"Total Volume: {volume_str}"]
    end_date = market.get("endDate") or market.get("end_date_iso")
    if end_date and isinstance(end_date, str):
        lines.append(f"Ends: {end_date[:10]}")
    slug = _first_present(market, "slug", "market_slug")
    if slug:
        lines.append(f"URL: https://polymarket.com/event/{slug}")
    return "\n".join(lines)


def _normalize_search_results(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("events", "markets", "data", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


# ---------------------------------------------------------------------------
# Local event store — fetch once per session, search locally for all queries
# ---------------------------------------------------------------------------

_LOCAL_STORE_CACHE_KEY = ("polymarket_local_event_store",)
_LOCAL_STORE_TTL = 1800  # 30 minutes
_LOCAL_STORE_SIZE = 200  # number of high-volume events to pre-fetch
_MIN_VOLUME = 1_000     # noise floor — filter spam/test markets; LLM judges significance


def _get_event_volume(event: dict[str, Any]) -> float:
    """Extract the best available volume figure from an event dict."""
    raw = _first_present(event, "volume", "volume24hr", "volumeNum")
    return _safe_float(raw) or 0.0


def _get_local_event_store(include_closed: bool = False) -> list[dict[str, Any]]:
    """Return a broad set of active Polymarket events, fetched once per session.

    The first call hits the ``/events`` endpoint for up to
    ``_LOCAL_STORE_SIZE`` high-volume events and caches the result.
    Subsequent calls return the cache.
    """
    from tradingagents.dataflows.session_cache import SessionCache

    cache = SessionCache.get_instance()
    store_key = (*_LOCAL_STORE_CACHE_KEY, include_closed)

    cached = cache.get(store_key)
    if cached is not None:
        return cached

    try:
        events = _fetch_json(
            "/events",
            {
                "closed": str(include_closed).lower(),
                "limit": _LOCAL_STORE_SIZE,
                "order": "volume24hr",
                "ascending": "false",
            },
        )
    except (urllib.error.URLError, urllib.error.HTTPError):
        events = []

    if not isinstance(events, list):
        events = []

    # Keep only valid dicts with meaningful volume
    events = [
        e for e in events
        if isinstance(e, dict) and _get_event_volume(e) >= _MIN_VOLUME
    ]
    cache.put(store_key, events, ttl_seconds=_LOCAL_STORE_TTL)
    return events


def _build_haystack(event: dict[str, Any]) -> str:
    """Concatenate all searchable text for an event into one lower-case string."""
    parts = [
        str(_first_present(event, "title", "question") or ""),
        str(event.get("description") or ""),
    ]
    for market in event.get("markets") or []:
        if isinstance(market, dict):
            parts.append(
                str(_first_present(market, "question", "title") or "")
            )
    return " ".join(parts).lower()


def _score_event(haystack: str, tokens: list[str]) -> int:
    """Return the count of query tokens found in the haystack (0 = no match)."""
    return sum(1 for t in tokens if t in haystack)


def _search_local_store(
    query: str, limit: int, include_closed: bool = False,
) -> list[dict[str, Any]]:
    """Search the local event store with multi-token fuzzy matching.

    Each token in the query is checked independently against the event's
    title, description, and market questions.  Events are ranked by how
    many tokens matched so that partial overlaps still surface results.
    A match requires at least one token to be present.
    """
    events = _get_local_event_store(include_closed)
    tokens = [t for t in query.lower().split() if len(t) >= 2]
    if not tokens:
        return []

    scored: list[tuple[int, dict[str, Any]]] = []
    for event in events:
        haystack = _build_haystack(event)
        score = _score_event(haystack, tokens)
        if score > 0:
            scored.append((score, event))

    # Sort by descending token-match count
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [event for _, event in scored[:limit]]


def _search_events(
    query: str, limit: int, include_closed: bool = False,
) -> list[dict[str, Any]]:
    """Search for Polymarket events with a three-tier strategy:

    1. **Exact SessionCache** — identical (query, limit) seen before.
    2. **Local event store** — fuzzy multi-token search across a cached
       set of ~200 high-volume events (one HTTP call per session).
    3. **API /search fallback** — only if local matching found nothing.
    """
    from tradingagents.dataflows.session_cache import SessionCache

    # ── Tier 1: exact query cache ────────────────────────────────────
    cache = SessionCache.get_instance()
    cache_key = ("polymarket_search", query.lower().strip(), limit, include_closed)

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # ── Tier 2: local event store (fuzzy) ────────────────────────────
    local_results = _search_local_store(query, limit, include_closed)
    if local_results:
        cache.put(cache_key, local_results, ttl_seconds=_LOCAL_STORE_TTL)
        return local_results

    # ── Tier 3: remote /search API ───────────────────────────────────
    try:
        data = _fetch_json("/search", {"query": query, "limit": limit})
        results = [
            r for r in _normalize_search_results(data)
            if _get_event_volume(r) >= _MIN_VOLUME
        ]
        if results:
            results = results[:limit]
            cache.put(cache_key, results, ttl_seconds=_LOCAL_STORE_TTL)
            return results
    except urllib.error.HTTPError:
        pass

    return []


# ---------------------------------------------------------------------------
# Public LangChain tool
# ---------------------------------------------------------------------------

@tool
def get_prediction_market_data(query: str, limit: int = 5) -> str:
    """Search Polymarket prediction markets for events matching a query.

    Returns formatted summaries of event odds, volume, and end dates.
    Use this to gauge market-implied probabilities for macro events,
    policy decisions, elections, crypto, rates, and geopolitics.

    Args:
        query: Search text (e.g. "fed rate cut", "recession", "bitcoin",
               company name, or sector keyword).
        limit: Maximum number of events to return (default 5).
    """
    try:
        results = _search_events(query, limit)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        return f"Polymarket API request failed: {exc}"

    if not results:
        return f"No Polymarket events found for query: {query}"

    parts: list[str] = []
    for item in results:
        if item.get("markets"):
            parts.append(_format_event_summary(item))
        else:
            parts.append(_format_market_summary(item))

    return "\n\n".join(parts)

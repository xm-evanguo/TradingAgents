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

    volume = _first_present(event, "volume", "volume24hr")
    if volume is not None:
        label = "24h volume" if event.get("volume24hr") is not None else "Volume"
        lines.append(f"Volume: {label} {_format_money(volume)}")

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
    lines = [question, f"Odds: {shown}{volume_part}"]
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


def _search_events(
    query: str, limit: int, include_closed: bool = False,
) -> list[dict[str, Any]]:
    params = {"query": query, "limit": limit}
    try:
        data = _fetch_json("/search", params)
        results = _normalize_search_results(data)
        if results:
            return results[:limit]
    except urllib.error.HTTPError:
        pass

    # Fallback: fetch high-volume events and filter locally
    events = _fetch_json(
        "/events",
        {
            "closed": str(include_closed).lower(),
            "limit": max(limit * 8, 50),
            "order": "volume24hr",
            "ascending": "false",
        },
    )
    if not isinstance(events, list):
        return []

    lowered = query.lower()
    matches: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        haystacks = [
            str(_first_present(event, "title", "question") or "").lower(),
            str(event.get("description") or "").lower(),
        ]
        if any(lowered in h for h in haystacks):
            matches.append(event)
            continue
        markets = event.get("markets") or []
        if isinstance(markets, list):
            for market in markets:
                if isinstance(market, dict):
                    q = str(
                        _first_present(market, "question", "title") or ""
                    ).lower()
                    if lowered in q:
                        matches.append(event)
                        break

    return matches[:limit]


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

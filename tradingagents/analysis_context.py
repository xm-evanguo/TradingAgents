from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


MARKET_LOOK_BACK_DAYS = 60
NEWS_LOOK_BACK_DAYS = 7
SOCIAL_LOOK_BACK_DAYS = 7
GLOBAL_NEWS_LIMIT = 10


def _parse_trade_date(trade_date: str) -> datetime:
    return datetime.strptime(trade_date, "%Y-%m-%d")


def get_default_analysis_context(trade_date: str) -> dict[str, Any]:
    trade_dt = _parse_trade_date(trade_date)

    market_start_date = (trade_dt - timedelta(days=MARKET_LOOK_BACK_DAYS)).strftime(
        "%Y-%m-%d"
    )
    news_start_date = (trade_dt - timedelta(days=NEWS_LOOK_BACK_DAYS)).strftime(
        "%Y-%m-%d"
    )
    social_start_date = (trade_dt - timedelta(days=SOCIAL_LOOK_BACK_DAYS)).strftime(
        "%Y-%m-%d"
    )

    return {
        "trade_date": trade_date,
        "market_start_date": market_start_date,
        "market_end_date": trade_date,
        "market_look_back_days": MARKET_LOOK_BACK_DAYS,
        "news_start_date": news_start_date,
        "news_end_date": trade_date,
        "news_look_back_days": NEWS_LOOK_BACK_DAYS,
        "global_news_limit": GLOBAL_NEWS_LIMIT,
        "social_start_date": social_start_date,
        "social_end_date": trade_date,
        "social_look_back_days": SOCIAL_LOOK_BACK_DAYS,
        "fundamentals_date": trade_date,
    }


def build_default_analysis_message(ticker: str, trade_date: str) -> str:
    context = get_default_analysis_context(trade_date)

    return (
        f"Analyze {ticker} for trade date {trade_date}.\n"
        "Use the default analysis windows below whenever a tool requires date "
        "arguments. Do not ask the user to clarify date ranges unless the "
        "ticker itself is ambiguous.\n"
        f"- Market OHLCV window: {context['market_start_date']} to "
        f"{context['market_end_date']}\n"
        f"- Technical indicator lookback: {context['market_look_back_days']} days "
        f"ending on {trade_date}\n"
        f"- Company news window: {context['news_start_date']} to "
        f"{context['news_end_date']}\n"
        f"- Global news lookback: {context['news_look_back_days']} days ending on "
        f"{trade_date}, limit {context['global_news_limit']}\n"
        f"- Social/news context window: {context['social_start_date']} to "
        f"{context['social_end_date']}\n"
        f"- Fundamentals snapshot date: {context['fundamentals_date']}"
    )

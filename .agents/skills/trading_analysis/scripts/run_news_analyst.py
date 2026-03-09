#!/usr/bin/env python3
"""
News Analyst Data Collector
Fetches recent company news, global macro news, and insider transactions.
No LLM required — calls data vendors directly.

Usage:
    python run_news_analyst.py <TICKER> <DATE>
    python run_news_analyst.py NVDA 2026-02-25
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from tradingagents.dataflows.config import set_config
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.analysis_context import get_default_analysis_context


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "message": "Usage: run_news_analyst.py <TICKER> <DATE>\n  Example: run_news_analyst.py NVDA 2026-02-25"
        }, indent=2))
        sys.exit(1)

    ticker = sys.argv[1].upper()
    trade_date = sys.argv[2]

    try:
        datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"status": "error", "message": f"Invalid date format: '{trade_date}'. Use YYYY-MM-DD."}))
        sys.exit(1)

    config = DEFAULT_CONFIG.copy()
    config["data_vendors"] = {"news_data": "yfinance"}
    set_config(config)

    analysis_context = get_default_analysis_context(trade_date)
    start_date = analysis_context["news_start_date"]

    result = {
        "ticker": ticker,
        "date": trade_date,
        "status": "success",
        "data": {}
    }

    # Company-specific news
    try:
        news = route_to_vendor(
            "get_news",
            ticker,
            start_date,
            analysis_context["news_end_date"],
        )
        result["data"]["company_news"] = news
    except Exception as e:
        result["data"]["company_news"] = f"Error: {e}"

    # Global macro news
    try:
        global_news = route_to_vendor(
            "get_global_news",
            trade_date,
            look_back_days=analysis_context["news_look_back_days"],
            limit=analysis_context["global_news_limit"],
        )
        result["data"]["global_news"] = global_news
    except Exception as e:
        result["data"]["global_news"] = f"Error: {e}"

    # Insider transactions
    try:
        insider = route_to_vendor("get_insider_transactions", ticker)
        result["data"]["insider_transactions"] = insider
    except Exception as e:
        result["data"]["insider_transactions"] = f"Error: {e}"

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

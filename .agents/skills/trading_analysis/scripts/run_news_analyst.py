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
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from tradingagents.dataflows.config import set_config
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.interface import route_to_vendor


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
        dt = datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"status": "error", "message": f"Invalid date format: '{trade_date}'. Use YYYY-MM-DD."}))
        sys.exit(1)

    config = DEFAULT_CONFIG.copy()
    config["data_vendors"] = {"news_data": "yfinance"}
    set_config(config)

    start_date = (dt - timedelta(days=7)).strftime("%Y-%m-%d")

    result = {
        "ticker": ticker,
        "date": trade_date,
        "status": "success",
        "data": {}
    }

    # Company-specific news
    try:
        news = route_to_vendor("get_news", ticker, start_date, trade_date)
        result["data"]["company_news"] = news
    except Exception as e:
        result["data"]["company_news"] = f"Error: {e}"

    # Global macro news
    try:
        global_news = route_to_vendor("get_global_news", trade_date, look_back_days=7, limit=10)
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

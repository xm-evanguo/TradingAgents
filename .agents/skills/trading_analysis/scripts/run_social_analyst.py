#!/usr/bin/env python3
"""
Social Media Analyst Data Collector
Fetches social media sentiment analysis for a given ticker using Grok/X API.
No LLM required — calls data vendors directly.

Note: Requires XAI_API_KEY in .env (Grok API). Will exit gracefully if unavailable.

Usage:
    python run_social_analyst.py <TICKER> <DATE>
    python run_social_analyst.py NVDA 2026-02-25
"""

import sys
import json
import os
from datetime import datetime
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
            "message": "Usage: run_social_analyst.py <TICKER> <DATE>\n  Example: run_social_analyst.py NVDA 2026-02-25"
        }, indent=2))
        sys.exit(1)

    ticker = sys.argv[1].upper()
    trade_date = sys.argv[2]

    try:
        datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"status": "error", "message": f"Invalid date format: '{trade_date}'. Use YYYY-MM-DD."}))
        sys.exit(1)

    # Check for XAI_API_KEY
    if not os.environ.get("XAI_API_KEY"):
        print(json.dumps({
            "ticker": ticker,
            "date": trade_date,
            "status": "skipped",
            "message": "XAI_API_KEY not set. Social media analysis requires Grok API access. Set XAI_API_KEY in your .env file."
        }, indent=2))
        sys.exit(0)

    config = DEFAULT_CONFIG.copy()
    config["data_vendors"] = {"social_media": "grok"}
    set_config(config)

    result = {
        "ticker": ticker,
        "date": trade_date,
        "status": "success",
        "data": {}
    }

    try:
        sentiment = route_to_vendor("get_social_media_sentiment", ticker, trade_date)
        result["data"]["social_media_sentiment"] = sentiment
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

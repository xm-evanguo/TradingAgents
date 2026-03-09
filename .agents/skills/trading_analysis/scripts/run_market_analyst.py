#!/usr/bin/env python3
"""
Market Analyst Data Collector
Fetches real-time stock price data and technical indicators for a given ticker.
No LLM required — calls data vendors directly.

Usage:
    python run_market_analyst.py <TICKER> <DATE>
    python run_market_analyst.py NVDA 2026-02-25
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import from TradingAgents project root
project_root = Path(__file__).resolve().parents[4]  # up from scripts/ -> trading_analysis/ -> skills/ -> .agents/ -> project root
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
            "message": "Usage: run_market_analyst.py <TICKER> <DATE>\n  Example: run_market_analyst.py NVDA 2026-02-25"
        }, indent=2))
        sys.exit(1)

    ticker = sys.argv[1].upper()
    trade_date = sys.argv[2]

    # Validate date format
    try:
        datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"status": "error", "message": f"Invalid date format: '{trade_date}'. Use YYYY-MM-DD."}))
        sys.exit(1)

    # Configure data vendors
    config = DEFAULT_CONFIG.copy()
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
    }
    set_config(config)

    analysis_context = get_default_analysis_context(trade_date)
    start_date = analysis_context["market_start_date"]
    end_date = analysis_context["market_end_date"]

    result = {
        "ticker": ticker,
        "date": trade_date,
        "status": "success",
        "data": {}
    }

    # Fetch OHLCV stock data
    try:
        stock_data = route_to_vendor("get_stock_data", ticker, start_date, end_date)
        result["data"]["stock_price"] = stock_data
    except Exception as e:
        result["data"]["stock_price"] = f"Error: {e}"

    # Fetch technical indicators
    indicators = ["close_50_sma", "close_200_sma", "macd", "boll", "rsi"]
    result["data"]["technical_indicators"] = {}

    for indicator in indicators:
        try:
            ind_data = route_to_vendor(
                "get_indicators",
                ticker,
                indicator,
                trade_date,
                look_back_days=analysis_context["market_look_back_days"],
            )
            result["data"]["technical_indicators"][indicator] = ind_data
        except Exception as e:
            result["data"]["technical_indicators"][indicator] = f"Error: {e}"

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

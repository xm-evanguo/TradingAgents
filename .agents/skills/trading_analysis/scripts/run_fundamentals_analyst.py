#!/usr/bin/env python3
"""
Fundamentals Analyst Data Collector
Fetches company financial statements: fundamentals, balance sheet, cash flow, income statement.
No LLM required — calls data vendors directly.

Usage:
    python run_fundamentals_analyst.py <TICKER> <DATE>
    python run_fundamentals_analyst.py NVDA 2026-02-25
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


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "message": "Usage: run_fundamentals_analyst.py <TICKER> <DATE>\n  Example: run_fundamentals_analyst.py NVDA 2026-02-25"
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
    config["data_vendors"] = {"fundamental_data": "yfinance"}
    set_config(config)

    result = {
        "ticker": ticker,
        "date": trade_date,
        "status": "success",
        "data": {}
    }

    # Core fundamentals (P/E ratio, market cap, revenue, margins, etc.)
    try:
        fundamentals = route_to_vendor("get_fundamentals", ticker, trade_date)
        result["data"]["fundamentals"] = fundamentals
    except Exception as e:
        result["data"]["fundamentals"] = f"Error: {e}"

    # Balance sheet
    try:
        balance_sheet = route_to_vendor("get_balance_sheet", ticker, "quarterly", trade_date)
        result["data"]["balance_sheet"] = balance_sheet
    except Exception as e:
        result["data"]["balance_sheet"] = f"Error: {e}"

    # Cash flow statement
    try:
        cashflow = route_to_vendor("get_cashflow", ticker, "quarterly", trade_date)
        result["data"]["cash_flow"] = cashflow
    except Exception as e:
        result["data"]["cash_flow"] = f"Error: {e}"

    # Income statement
    try:
        income = route_to_vendor("get_income_statement", ticker, "quarterly", trade_date)
        result["data"]["income_statement"] = income
    except Exception as e:
        result["data"]["income_statement"] = f"Error: {e}"

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

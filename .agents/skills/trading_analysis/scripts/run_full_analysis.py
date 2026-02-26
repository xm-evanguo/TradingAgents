#!/usr/bin/env python3
"""
Full TradingAgents Pipeline Runner
Runs the complete analysis: all selected analysts → Bull/Bear researchers → Risk management → Final decision.
This DOES use LLMs and takes 2-5 minutes to complete.

Usage:
    python run_full_analysis.py <TICKER> <DATE> [OPTIONS]

Options:
    --analysts   Comma-separated list of analysts to run (default: market,news,fundamentals)
                 Choices: market, news, fundamentals, social
    --provider   LLM provider (default: from DEFAULT_CONFIG)
    --quick-model  Quick-thinking LLM model name
    --deep-model   Deep-thinking LLM model name
    --rounds     Max debate rounds (default: 1 for speed)

Examples:
    python run_full_analysis.py NVDA 2026-02-25
    python run_full_analysis.py NVDA 2026-02-25 --analysts market,news,fundamentals
    python run_full_analysis.py NVDA 2026-02-25 --provider openai --quick-model gpt-4o-mini --deep-model gpt-4o
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


def main():
    parser = argparse.ArgumentParser(description="Run full TradingAgents pipeline with LLM analysis")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., NVDA)")
    parser.add_argument("date", help="Trade date in YYYY-MM-DD format")
    parser.add_argument(
        "--analysts",
        default="market,news,fundamentals",
        help="Comma-separated list of analysts to run (default: market,news,fundamentals)"
    )
    parser.add_argument("--provider", help="LLM provider (e.g., openai, anthropic, deepseek)")
    parser.add_argument("--quick-model", help="Model for quick-thinking tasks")
    parser.add_argument("--deep-model", help="Model for deep-thinking tasks (debate, risk)")
    parser.add_argument("--rounds", type=int, default=1, help="Max debate/risk discussion rounds (default: 1)")

    args = parser.parse_args()

    ticker = args.ticker.upper()
    trade_date = args.date

    # Validate date
    try:
        datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"status": "error", "message": f"Invalid date format: '{trade_date}'. Use YYYY-MM-DD."}))
        sys.exit(1)

    # Parse analyst list
    valid_analysts = {"market", "news", "fundamentals", "social"}
    selected_analysts = [a.strip() for a in args.analysts.split(",")]
    invalid = [a for a in selected_analysts if a not in valid_analysts]
    if invalid:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid analyst(s): {invalid}. Choose from: {sorted(valid_analysts)}"
        }))
        sys.exit(1)

    # Build config
    config = DEFAULT_CONFIG.copy()
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
        "social_media": "grok",
    }
    config["max_debate_rounds"] = args.rounds
    config["max_risk_discuss_rounds"] = args.rounds

    if args.provider:
        config["llm_provider"] = args.provider
    if args.quick_model:
        config["quick_think_llm"] = args.quick_model
    if args.deep_model:
        config["deep_think_llm"] = args.deep_model

    print(f"[TradingAgents] Running full analysis for {ticker} on {trade_date}", file=sys.stderr)
    print(f"[TradingAgents] Analysts: {selected_analysts}", file=sys.stderr)
    print(f"[TradingAgents] LLM: {config['llm_provider']} / quick={config['quick_think_llm']} / deep={config['deep_think_llm']}", file=sys.stderr)
    print(f"[TradingAgents] This may take 2-5 minutes...", file=sys.stderr)

    try:
        ta = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            debug=False,
            config=config,
        )

        final_state, decision = ta.propagate(ticker, trade_date)

        result = {
            "ticker": ticker,
            "date": trade_date,
            "status": "success",
            "analysts_used": selected_analysts,
            "decision": decision,
            "reports": {
                "market_report": final_state.get("market_report", ""),
                "news_report": final_state.get("news_report", ""),
                "fundamentals_report": final_state.get("fundamentals_report", ""),
                "sentiment_report": final_state.get("sentiment_report", ""),
            },
            "investment_debate": {
                "bull_argument": final_state.get("investment_debate_state", {}).get("bull_history", ""),
                "bear_argument": final_state.get("investment_debate_state", {}).get("bear_history", ""),
                "judge_decision": final_state.get("investment_debate_state", {}).get("judge_decision", ""),
            },
            "risk_assessment": {
                "judge_decision": final_state.get("risk_debate_state", {}).get("judge_decision", ""),
            },
            "final_trade_decision": final_state.get("final_trade_decision", ""),
        }

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            "ticker": ticker,
            "date": trade_date,
            "status": "error",
            "message": str(e)
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

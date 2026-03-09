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
    --rounds     Max debate rounds, 1-5 (default: 1 for speed)

Examples:
    python run_full_analysis.py NVDA 2026-02-25
    python run_full_analysis.py NVDA 2026-02-25 --analysts market,news,fundamentals
    python run_full_analysis.py NVDA 2026-02-25 --rounds 2
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
from tradingagents.llm_clients.model_router import resolve_llm_plan


def _rounds_type(value: str) -> int:
    try:
        rounds = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("rounds must be an integer") from exc
    if rounds < 1 or rounds > 5:
        raise argparse.ArgumentTypeError("rounds must be between 1 and 5")
    return rounds


def main():
    parser = argparse.ArgumentParser(description="Run full TradingAgents pipeline with LLM analysis")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., NVDA)")
    parser.add_argument("date", help="Trade date in YYYY-MM-DD format")
    parser.add_argument(
        "--analysts",
        default="market,news,fundamentals",
        help="Comma-separated list of analysts to run (default: market,news,fundamentals)"
    )
    parser.add_argument(
        "--rounds",
        type=_rounds_type,
        default=1,
        help="Max debate/risk discussion rounds (1-5, default: 1)",
    )

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

    llm_plan = resolve_llm_plan()
    config["llm_provider"] = llm_plan["deep_provider"]
    config["deep_think_provider"] = llm_plan["deep_provider"]
    config["quick_think_provider"] = llm_plan["quick_provider"]
    config["deep_backend_url"] = llm_plan["deep_backend_url"]
    config["quick_backend_url"] = llm_plan["quick_backend_url"]
    config["deep_think_llm"] = llm_plan["deep_model"]
    config["quick_think_llm"] = llm_plan["quick_model"]

    print(f"[TradingAgents] Running full analysis for {ticker} on {trade_date}", file=sys.stderr)
    print(f"[TradingAgents] Analysts: {selected_analysts}", file=sys.stderr)
    print(
        f"[TradingAgents] LLM routing: deep={config['deep_think_provider']}:{config['deep_think_llm']} "
        f"/ quick={config['quick_think_provider']}:{config['quick_think_llm']}",
        file=sys.stderr,
    )
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

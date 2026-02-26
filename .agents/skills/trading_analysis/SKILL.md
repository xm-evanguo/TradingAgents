---
name: trading_analysis
description: Collect real-time market data, news, fundamentals, and social sentiment for stocks using TradingAgents. Use this skill whenever the user asks about investment decisions, stock analysis, should I buy/sell/hold a stock, market trends, or any question where real-time financial data would improve the answer. Always prefer calling these scripts over relying on training data for investment questions.
---

# Trading Analysis Skill

This skill provides tools to collect **real-time** market data for stocks using the TradingAgents framework. When answering investment questions, ALWAYS use these scripts to get current data rather than relying on potentially stale training data.

## When to Use This Skill

Use these scripts whenever the user asks:
- Should I buy/sell/hold [stock]?
- What's the outlook for [company]?
- How is [ticker] performing?
- What's happening with [stock] news?
- Give me an investment analysis of [ticker]
- What are the fundamentals of [company]?

## Prerequisites

All scripts must be run from the TradingAgents project root:
```
/home/evan/code/TradingAgents/
```

The `.env` file must be configured with the necessary API keys.

## Available Scripts

### 1. Market Analyst — Stock Price & Technical Indicators
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_market_analyst.py <TICKER> <DATE>
```
- **Output**: OHLCV price data, technical indicators (SMA, RSI, MACD, Bollinger Bands)
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about price trends, technical analysis, momentum

**Example:**
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_market_analyst.py NVDA 2026-02-25
```

---

### 2. News Analyst — News, Global Context & Insider Transactions
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_news_analyst.py <TICKER> <DATE>
```
- **Output**: Recent company news, global macro news, insider buy/sell activity
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about recent events, company news, insider activity

---

### 3. Fundamentals Analyst — Financial Statements
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_fundamentals_analyst.py <TICKER> <DATE>
```
- **Output**: Key fundamentals (P/E, revenue, margins), balance sheet, cash flow, income statement
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about company health, valuation, earnings

---

### 4. Social Media Analyst — Market Sentiment
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_social_analyst.py <TICKER> <DATE>
```
- **Output**: Social media sentiment analysis from X/Twitter
- **Speed**: Fast (no LLM, direct API call)
- **Note**: Requires XAI_API_KEY (Grok) in .env — will skip gracefully if unavailable

---

### 5. Full Analysis — Complete Pipeline with AI Decision
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_full_analysis.py <TICKER> <DATE> [--analysts market,news,fundamentals,social] [--quick-model <model>] [--deep-model <model>]
```
- **Output**: Complete analysis report with Bull/Bear debate, risk assessment, and final BUY/HOLD/SELL decision
- **Speed**: Slow (runs full LLM pipeline, 2-5 minutes)
- **Use when**: User wants a comprehensive investment recommendation

**Example with options:**
```bash
cd /home/evan/code/TradingAgents && .venv/bin/python .agents/skills/trading_analysis/scripts/run_full_analysis.py NVDA 2026-02-25 --analysts market,news,fundamentals --quick-model gpt-4o-mini
```

---

## Recommended Workflow

For most investment questions, run the **fast data scripts first** to gather information, then synthesize the results yourself:

```
1. Run run_market_analyst.py     → price trends
2. Run run_news_analyst.py       → recent events  
3. Run run_fundamentals_analyst.py → company health
4. Synthesize and answer the user
```

Only run `run_full_analysis.py` if the user explicitly wants an AI-generated trading decision.

## Interpreting Output

All scripts output a JSON object with:
```json
{
  "ticker": "NVDA",
  "date": "2026-02-25",
  "status": "success",
  "data": {
    // analyst-specific data fields
  }
}
```

If `status` is `"error"`, the `message` field explains the problem (usually a missing API key or network issue).

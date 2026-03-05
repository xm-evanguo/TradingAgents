---
name: trading-analysis
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

Run all scripts from the TradingAgents project root (the directory containing `pyproject.toml`).
In this workspace, that root is:
`/home/evan/my_skills/TradingAgents`

The `.env` file must be configured with the necessary API keys.
If you want OAuth routes (Codex/Gemini CLI), pi-ai-server must be reachable and authenticated.
TradingAgents will auto-start pi-ai-server for localhost URLs when `PI_AI_SERVER_CMD`
or the default `~/code/pi-mono/packages/ai-server/*` paths are available.
Use `PI_AI_SERVER_CMD`, `PI_AI_SERVER_CWD`, and `PI_AI_SERVER_URL` for custom setups.
Use `uv run python` for script execution so commands do not depend on a fixed `.venv` path.

## Available Scripts

### 1. Market Analyst - Stock Price & Technical Indicators
```bash
uv run python .agents/skills/trading_analysis/scripts/run_market_analyst.py <TICKER> <DATE>
```
- **Output**: OHLCV price data, technical indicators (SMA, RSI, MACD, Bollinger Bands)
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about price trends, technical analysis, momentum

**Example:**
```bash
uv run python .agents/skills/trading_analysis/scripts/run_market_analyst.py NVDA 2026-02-25
```

---

### 2. News Analyst - News, Global Context & Insider Transactions
```bash
uv run python .agents/skills/trading_analysis/scripts/run_news_analyst.py <TICKER> <DATE>
```
- **Output**: Recent company news, global macro news, insider buy/sell activity
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about recent events, company news, insider activity

---

### 3. Fundamentals Analyst - Financial Statements
```bash
uv run python .agents/skills/trading_analysis/scripts/run_fundamentals_analyst.py <TICKER> <DATE>
```
- **Output**: Key fundamentals (P/E, revenue, margins), balance sheet, cash flow, income statement
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about company health, valuation, earnings

---

### 4. Social Media Analyst - Market Sentiment
```bash
uv run python .agents/skills/trading_analysis/scripts/run_social_analyst.py <TICKER> <DATE>
```
- **Output**: Social media sentiment analysis from X/Twitter
- **Speed**: Fast (no LLM, direct API call)
- **Note**: Requires XAI_API_KEY (Grok) in .env - will skip gracefully if unavailable

---

### 5. Full Analysis - Complete Pipeline with AI Decision
```bash
uv run python .agents/skills/trading_analysis/scripts/run_full_analysis.py <TICKER> <DATE> [--analysts market,news,fundamentals,social] [--rounds <N>]
```
- **Output**: Complete analysis report with Bull/Bear debate, risk assessment, and final BUY/HOLD/SELL decision
- **Speed**: Slow (runs full LLM pipeline, 2-5 minutes)
- **Use when**: User explicitly asks for an AI-generated final decision, or a comprehensive end-to-end analysis is needed
- **Debate rounds**: Supported via `--rounds <N>` (applies to both investment debate and risk discussion; default is `1`)
- **LLM routing**: Model/provider routing is automatic. Do not manually choose model names in this workflow.
- **Routing priority**:
  - If Codex OAuth is available: deep=`gpt-5.2`, quick=`gpt-5.2`
  - Else if Gemini CLI OAuth is available: deep=`gemini-3.1-pro-preview`, quick=`gemini-3.1-flash-preview`
  - Else API-key fallback: `MiniMax-M2.5` -> `kimi-k2.5` -> DeepSeek (`deepseek-reasoner` deep, `deepseek-chat` quick)

**Example with options:**
```bash
uv run python .agents/skills/trading_analysis/scripts/run_full_analysis.py NVDA 2026-02-25 --analysts market,news,fundamentals --rounds 2
```

---

## Recommended Workflow

Choose scripts based on user intent. Run only the minimum set needed, then synthesize:

```
1. Price/technical question -> run_market_analyst.py
2. News/event question -> run_news_analyst.py
3. Financial health/valuation question -> run_fundamentals_analyst.py
4. Sentiment question -> run_social_analyst.py
5. Multi-factor question -> run any relevant combination above
6. Synthesize and answer the user
```

Run `run_full_analysis.py` only when the user explicitly requests it, or when a comprehensive AI decision workflow is truly required.

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

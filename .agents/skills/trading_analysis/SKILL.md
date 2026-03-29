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

## Default Analysis Windows

Manual analyst scripts and graph-driven workflows are expected to stay aligned on default windows.
Current defaults are:
- Market OHLCV window: prior `60` calendar days ending on `trade_date`
- Technical indicator lookback: `60` days ending on `trade_date`
- Company news window: prior `7` days ending on `trade_date`
- Global news window: prior `7` days ending on `trade_date` with limit `10`
- Fundamentals snapshot: `trade_date`
- Social sentiment: `trade_date`; graph/full-analysis also pairs this with recent company-news context over the prior `7` days

Do not rely on the LLM to infer or ask for these date ranges when the workflow already knows `trade_date`.

## Available Scripts

### 1. Market Analyst - Stock Price & Technical Indicators
```bash
uv run python .agents/skills/trading_analysis/scripts/run_market_analyst.py <TICKER> <DATE>
```
- **Output**: OHLCV price data, technical indicators (SMA, RSI, MACD, Bollinger Bands)
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about price trends, technical analysis, momentum
- **Default window**: Fetches price data over the prior `60` days ending on `<DATE>` and computes indicators with a `60`-day lookback ending on `<DATE>`

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
- **Default window**: Company/global news use the prior `7` days ending on `<DATE>`; insider transactions are fetched directly for the ticker

---

### 3. Fundamentals Analyst - Financial Statements
```bash
uv run python .agents/skills/trading_analysis/scripts/run_fundamentals_analyst.py <TICKER> <DATE>
```
- **Output**: Key fundamentals (P/E, revenue, margins), balance sheet, cash flow, income statement
- **Speed**: Fast (no LLM, direct API call)
- **Use when**: User asks about company health, valuation, earnings
- **Default window**: Uses `<DATE>` as the fundamentals snapshot date for all statement lookups

---

### 4. Social Media Analyst - Market Sentiment
```bash
uv run python .agents/skills/trading_analysis/scripts/run_social_analyst.py <TICKER> <DATE>
```
- **Output**: Social media sentiment analysis from X/Twitter
- **Speed**: Fast (no LLM, direct API call)
- **Note**: Requires XAI_API_KEY (Grok) in .env - will skip gracefully if unavailable
- **Default window**: Standalone script queries sentiment at `<DATE>`; graph/full-analysis additionally provides recent company-news context over the prior `7` days

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
- **Graph/manual consistency**: Full analysis injects the same default windows into graph state and analyst prompts so the model should not need to ask for date-range clarification
- **Routing priority**:
  - Deep prefers Codex OAuth (`gpt-5.4`), then Gemini CLI OAuth (`gemini-3.1-pro-preview`), then API-key fallback `kimi-k2.5` -> DeepSeek (`deepseek-reasoner`)
  - Quick prefers Gemini CLI OAuth (`gemini-3-flash-preview`), otherwise API-key fallback `kimi-k2.5` -> DeepSeek (`deepseek-chat`)
  - If both Codex OAuth and Gemini CLI OAuth are available, the expected split is deep=`gpt-5.4` and quick=`gemini-3-flash-preview`

**Example with options:**
```bash
uv run python .agents/skills/trading_analysis/scripts/run_full_analysis.py NVDA 2026-02-25 --analysts market,news,fundamentals --rounds 2
```

- **E2E smoke-test preset**: For lightweight end-to-end validation, use ticker `WDAY`, force both deep and quick routes to `deepseek:deepseek-chat`, keep the run at `Shallow` depth (`--rounds 1`), and limit analysts to `market` so the workflow only covers technical analysis.

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

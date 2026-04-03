---
name: tradingagents-repo
description: Use the TradingAgents repository at /home/evan/my_skills/TradingAgents as an external tool for real-time stock analysis, investment research, and targeted TradingAgents CLI or script runs. Trigger this skill when Codex should use this repo directly instead of relying on stale model knowledge or reading the human-facing README, especially for technical analysis, news analysis, fundamentals, sentiment, LLM routing behavior, or lightweight end-to-end validation.
---

# TradingAgents Repo Skill

Use this repository as an execution tool, not as general reference prose.
Do not start with `README.md` unless the user explicitly asks for human-oriented setup or project documentation.

## Repo Root

Run all commands from:
`/home/evan/my_skills/TradingAgents`

Prefer `uv run python` so execution does not depend on a fixed virtualenv path.

## Use This Repo For

- Real-time stock analysis with current market data
- Technical analysis only runs
- News, insider, macro, and prediction-market context
- Fundamentals snapshots
- Social sentiment checks
- Full TradingAgents pipeline runs when the user explicitly wants an AI decision
- Verifying current LLM routing or research-depth behavior implemented in code

## Stable Entry Points

Prefer these scripts instead of reconstructing repo internals manually:

- `uv run python .agents/skills/trading_analysis/scripts/run_market_analyst.py <TICKER> <DATE>`
- `uv run python .agents/skills/trading_analysis/scripts/run_news_analyst.py <TICKER> <DATE>`
- `uv run python .agents/skills/trading_analysis/scripts/run_fundamentals_analyst.py <TICKER> <DATE>`
- `uv run python .agents/skills/trading_analysis/scripts/run_social_analyst.py <TICKER> <DATE>`
- `uv run python .agents/skills/trading_analysis/scripts/run_full_analysis.py <TICKER> <DATE> [--analysts ...] [--rounds N]`

Use the interactive CLI only when the user specifically wants the full CLI flow:

- `uv run python -m cli.main analyze`

## Selection Rules

Choose the smallest workflow that answers the request:

1. Price action, indicators, trend, momentum, RSI, MACD, Bollinger Bands:
   use `run_market_analyst.py`
2. Company news, macro context, insider activity, prediction markets:
   use `run_news_analyst.py`
3. Valuation, financial health, statements:
   use `run_fundamentals_analyst.py`
4. Social sentiment:
   use `run_social_analyst.py`
5. Multi-factor but still deterministic:
   run only the relevant analyst scripts and synthesize the answer yourself
6. Final AI recommendation, debate, risk discussion, or full end-to-end workflow:
   use `run_full_analysis.py`

Do not run the full analysis pipeline unless the user explicitly wants a comprehensive AI decision or the task clearly requires it.

## Required Runtime Assumptions

- Keep secrets in `.env` or Doppler-backed environment variables.
- `ALPHA_VANTAGE_API_KEY` is needed for market-data flows.
- `XAI_API_KEY` is needed for social sentiment; missing it should be treated as a partial capability, not a hard failure for unrelated tasks.
- OAuth routes depend on a reachable `pi-ai-server`.
- For current `badlogic/pi-mono`, clone `https://github.com/badlogic/pi-mono.git`, build `packages/ai`, and use this repo's `scripts/pi_ai_server_compat.mjs` compatibility server when needed.

## LLM Routing Rules

Assume automatic routing unless the user explicitly asks to override implementation details.
Current routing intent in this repo is:

- Deep priority: Codex OAuth -> Gemini CLI OAuth -> `MiniMax-M2.7` -> `kimi-k2.5` -> DeepSeek (`deepseek-reasoner`)
- Quick priority: Gemini CLI OAuth (`gemini-3-flash-preview`) -> `MiniMax-M2.7` -> `kimi-k2.5` -> DeepSeek (`deepseek-chat`)
- If the CLI does not explicitly override the model, it should try the highest-priority default route first and then automatically fall through to the next provider/model in order whenever the current default route cannot be used, or when a request to that route fails for provider/model availability, auth, API-key, rate-limit, or similar upstream request errors.

Do not introduce workflows that ask the user to manually pick deep or quick models unless the task is specifically about debugging routing.

## Research Depth Rules

Honor the current CLI mapping:

- `Deep = 3` rounds
- `Shallow = 1` round

`cli/main.py` applies the selected depth to both debate rounds and risk discussion rounds.

## Default Analysis Windows

When the workflow already knows `trade_date`, pass defaults explicitly instead of asking the user again:

- Market data window: prior `60` days ending on `trade_date`
- Technical indicator lookback: `60` days ending on `trade_date`
- Company news window: prior `7` days ending on `trade_date`
- Global news window: prior `7` days ending on `trade_date`
- Fundamentals snapshot: `trade_date`
- Social sentiment: `trade_date`, with recent company-news context over the prior `7` days in graph-driven runs

## E2E Smoke-Test Preset

For lightweight end-to-end validation, use this exact preset:

- Ticker: `WDAY`
- Deep model: `deepseek-chat`
- Quick model: `deepseek-chat`
- Research depth: `Shallow`
- Analysts: `market` only

This preset intentionally limits the run to technical analysis.

## Output Contract

The analyst scripts return JSON with a top-level structure like:

```json
{
  "ticker": "NVDA",
  "date": "2026-02-25",
  "status": "success",
  "data": {}
}
```

If `status` is `error`, report the failure directly and distinguish between:

- missing credentials
- provider/network failures
- unsupported workflow assumptions

Do not pretend the repo succeeded when the script returned an error payload.

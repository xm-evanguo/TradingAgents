# Repository Guidelines

## Project Structure & Module Organization
- `tradingagents/` contains core package code.
- `tradingagents/agents/` holds analyst, researcher, trader, and risk-management agents.
- `tradingagents/graph/` defines orchestration and signal propagation logic.
- `tradingagents/dataflows/` contains market/news/fundamental data adapters (for example `y_finance.py`, `alpha_vantage_*.py`).
- `tradingagents/llm_clients/` provides provider-specific LLM client implementations.
- `tradingagents/prompts/` stores Jinja2 prompt templates.
- `cli/` contains the Typer CLI entrypoint and terminal UI helpers.
- `assets/` is documentation/media only; runtime logic should stay out of this folder.

## Build, Test, and Development Commands
```bash
# install dependencies
pip install -r requirements.txt

# editable install with CLI script (tradingagents)
pip install -e .

# run the interactive CLI workflow
python -m cli.main analyze
# or, after install:
tradingagents analyze

# run package usage example
python main.py

# lightweight smoke test script
python test.py
```

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation.
- Use `snake_case` for functions/variables/modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Keep public functions typed when practical, and prefer small, composable helpers over long monolithic functions.
- Match existing module patterns (`*_analyst.py`, `*_researcher.py`, `*_client.py`) when adding new components.

## Testing Guidelines
- Current validation is script-based (`test.py`), with no enforced coverage gate yet.
- For new features, add focused tests close to the modified domain (dataflow, graph, or CLI behavior) and include at least one failure-path case.
- Before opening a PR, run affected flows locally (`python -m cli.main analyze` and any targeted scripts) and note what you validated.

## Commit & Pull Request Guidelines
- Recent history follows Conventional Commit-style prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `security:`.
- Keep commits scoped and imperative (example: `feat: add Grok social media adapter`).
- PRs should include: summary, key design choices, local verification steps, and any config/env changes.
- Link related issues and include terminal screenshots only when CLI output changes materially.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and set required keys (`OPENAI_API_KEY`, `ALPHA_VANTAGE_API_KEY`, etc.).
- Never commit secrets, local report outputs, or provider tokens.

## LLM Routing Rules
- Model/provider selection is automatic by default. Do not add new prompts that ask users to manually pick deep/quick models in CLI workflows.
- Routing order:
  - If Codex OAuth is available: deep=`gpt-5.4`, quick=`gpt-5.4` (provider `codex`)
  - Else if Gemini CLI OAuth is available: deep=`gemini-3.1-pro-preview`, quick=`gemini-3.1-flash-preview` (provider `google-gemini-cli`)
  - Else API-key fallback priority: `MiniMax-M2.5` -> `kimi-k2.5` -> DeepSeek (`deepseek-reasoner` for deep, `deepseek-chat` for quick)
- Keep these rules consistent across `cli/main.py`, `tradingagents/llm_clients/model_router.py`, `README.md`, and skill docs when making changes.

## Research Depth Rules
- Keep CLI research depth aligned with defaults unless there is a deliberate reason not to.
- Current mapping: `Deep = 3` rounds, `Shallow = 1` round.
- `cli/main.py` applies the selected value to both `max_debate_rounds` and `max_risk_discuss_rounds`.

## Analysis Window Defaults
- Keep manual analyst scripts and graph-driven workflows aligned on default analysis windows.
- Current defaults: market data and indicators use the prior `60` days ending on `trade_date`; company/global news use the prior `7` days ending on `trade_date`; fundamentals use `trade_date` as the snapshot date; social sentiment uses `trade_date` with recent-news context from the prior `7` days.
- Do not rely on the LLM to infer or ask for these defaults when the workflow already knows `trade_date`; pass the defaults explicitly in prompts/state.

import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    # Providers: google-gemini-cli (OAuth via pi-ai-server), codex (OAuth via pi-ai-server),
    #            openai, google, xai (API key via pi-ai-server),
    #            kimi, deepseek (direct API)
    "llm_provider": "google-gemini-cli",
    "deep_think_llm": "gemini-2.5-pro",
    "quick_think_llm": "gemini-2.5-flash",
    "deep_think_provider": None,
    "quick_think_provider": None,
    "backend_url": None,
    "deep_backend_url": None,
    "quick_backend_url": None,
    # Provider-specific thinking configuration
    "google_thinking_level": "high",      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    # Debate and discussion settings
    "max_debate_rounds": 3,
    "max_risk_discuss_rounds": 3,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: alpha_vantage, yfinance
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance
        "fundamental_data": "yfinance",      # Options: alpha_vantage, yfinance
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance
        "social_media": "grok",              # Options: grok (requires XAI_API_KEY)
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
}

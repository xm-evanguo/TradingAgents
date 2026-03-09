import os
from typing import Dict, Optional

from .pi_ai_server_manager import (
    DEFAULT_PI_AI_SERVER_URL,
    fetch_oauth_token,
)

_API_KEY_PROVIDER_PRIORITY = (
    ("minimax", "MINIMAX_API_KEY", "https://api.minimax.io/anthropic"),
    ("kimi", "MOONSHOT_API_KEY", "https://api.moonshot.ai/v1"),
    ("deepseek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/v1"),
)

DEFAULT_CODEX_MODEL = "gpt-5.4"


def _has_pi_ai_oauth(provider_id: str, server_url: str) -> bool:
    return bool(fetch_oauth_token(provider_id, server_url))


def _api_key_model(provider: str, role: str) -> str:
    if provider == "minimax":
        return "MiniMax-M2.5"
    if provider == "kimi":
        return "kimi-k2.5"
    if provider == "deepseek":
        return "deepseek-reasoner" if role == "deep" else "deepseek-chat"
    raise ValueError(f"Unsupported API-key provider: {provider}")


def _pick_api_key_provider(role: str) -> Optional[Dict[str, str]]:
    for provider, env_key, backend_url in _API_KEY_PROVIDER_PRIORITY:
        if os.getenv(env_key):
            return {
                "provider": provider,
                "model": _api_key_model(provider, role),
                "backend_url": backend_url,
            }
    return None


def resolve_llm_plan() -> Dict[str, Optional[str]]:
    """Resolve deep/quick provider+model without manual model selection."""
    server_url = os.getenv("PI_AI_SERVER_URL", DEFAULT_PI_AI_SERVER_URL)
    has_codex_auth = _has_pi_ai_oauth("openai-codex", server_url)
    has_gemini_cli_auth = _has_pi_ai_oauth("google-gemini-cli", server_url)

    # Step 1: codex auth has highest priority.
    if has_codex_auth:
        return {
            "deep_provider": "codex",
            "deep_model": DEFAULT_CODEX_MODEL,
            "deep_backend_url": "",
            "quick_provider": "codex",
            "quick_model": DEFAULT_CODEX_MODEL,
            "quick_backend_url": "",
        }

    # Step 2: if no codex auth, use gemini-cli auth when available.
    if has_gemini_cli_auth:
        return {
            "deep_provider": "google-gemini-cli",
            "deep_model": "gemini-3.1-pro-preview",
            "deep_backend_url": "",
            "quick_provider": "google-gemini-cli",
            "quick_model": "gemini-3.1-flash-preview",
            "quick_backend_url": "",
        }

    # Step 3: If no OAuth auth, use API-key models by priority.
    deep = _pick_api_key_provider("deep")
    quick = _pick_api_key_provider("quick")

    if deep and quick:
        return {
            "deep_provider": deep["provider"],
            "deep_model": deep["model"],
            "deep_backend_url": deep["backend_url"],
            "quick_provider": quick["provider"],
            "quick_model": quick["model"],
            "quick_backend_url": quick["backend_url"],
        }

    raise RuntimeError(
        "No available LLM route. "
        "Set credentials for codex/gemini-cli auth or API keys for minimax/kimi/deepseek."
    )

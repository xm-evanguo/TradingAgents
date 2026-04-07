import os
from typing import Any, Dict, List

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
GEMINI_DEEP_MODEL = "gemini-3.1-pro-preview"
GEMINI_QUICK_MODEL = "gemini-3-flash-preview"


def _has_pi_ai_oauth(provider_id: str, server_url: str) -> bool:
    return bool(fetch_oauth_token(provider_id, server_url))


def _api_key_model(provider: str, role: str) -> str:
    if provider == "kimi":
        return "kimi-k2.5"
    if provider == "minimax":
        return "MiniMax-M2.7"
    if provider == "deepseek":
        return "deepseek-reasoner" if role == "deep" else "deepseek-chat"
    raise ValueError(f"Unsupported API-key provider: {provider}")


def _available_api_key_candidates(role: str) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    for provider, env_key, backend_url in _API_KEY_PROVIDER_PRIORITY:
        if os.getenv(env_key):
            candidates.append(
                {
                    "provider": provider,
                    "model": _api_key_model(provider, role),
                    "backend_url": backend_url,
                }
            )
    return candidates


def _resolve_role_candidates(
    role: str,
    *,
    has_codex_auth: bool,
    has_gemini_cli_auth: bool,
) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []

    if role == "deep":
        if has_codex_auth:
            candidates.append(
                {
                    "provider": "codex",
                    "model": DEFAULT_CODEX_MODEL,
                    "backend_url": "",
                }
            )
        if has_gemini_cli_auth:
            candidates.append(
                {
                    "provider": "google-gemini-cli",
                    "model": GEMINI_DEEP_MODEL,
                    "backend_url": "",
                }
            )
    elif role == "quick":
        if has_gemini_cli_auth:
            candidates.append(
                {
                    "provider": "google-gemini-cli",
                    "model": GEMINI_QUICK_MODEL,
                    "backend_url": "",
                }
            )
    else:
        raise ValueError(f"Unsupported role: {role}")

    candidates.extend(_available_api_key_candidates(role))
    return candidates


def resolve_llm_plan() -> Dict[str, Any]:
    """Resolve deep/quick provider+model without manual model selection."""
    server_url = os.getenv("PI_AI_SERVER_URL", DEFAULT_PI_AI_SERVER_URL)
    has_codex_auth = _has_pi_ai_oauth("openai-codex", server_url)
    has_gemini_cli_auth = _has_pi_ai_oauth("google-gemini-cli", server_url)
    deep_candidates = _resolve_role_candidates(
        "deep",
        has_codex_auth=has_codex_auth,
        has_gemini_cli_auth=has_gemini_cli_auth,
    )
    quick_candidates = _resolve_role_candidates(
        "quick",
        has_codex_auth=has_codex_auth,
        has_gemini_cli_auth=has_gemini_cli_auth,
    )
    deep = deep_candidates[0] if deep_candidates else None
    quick = quick_candidates[0] if quick_candidates else None

    if deep and quick:
        return {
            "deep_provider": deep["provider"],
            "deep_model": deep["model"],
            "deep_backend_url": deep["backend_url"],
            "deep_candidates": deep_candidates,
            "quick_provider": quick["provider"],
            "quick_model": quick["model"],
            "quick_backend_url": quick["backend_url"],
            "quick_candidates": quick_candidates,
        }

    raise RuntimeError(
        "No available LLM route. "
        "Deep requires codex/gemini-cli auth or API keys for minimax/kimi/deepseek. "
        "Quick requires gemini-cli auth or API keys for minimax/kimi/deepseek."
    )

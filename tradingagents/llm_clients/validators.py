"""Model name validators for each provider.

Only validates model names - does NOT enforce limits.
Let LLM providers use their own defaults for unspecified params.
"""

# pi-ai passes validation through to the server which knows all models.
# For deepseek (direct OpenAI-compat path) we keep the explicit list.

_PI_AI_PROVIDERS = {
    "google-gemini-cli",
    "openai-codex",
    "openai",
    "google",
    "xai",
    "kimi-coding",
}

VALID_MODELS = {
    "deepseek": [
        "deepseek-chat",
        "deepseek-reasoner",
    ],
}


def validate_model(provider: str, model: str) -> bool:
    """Check if model name is valid for the given provider.

    For pi-ai-backed providers, ollama, openrouter - any model is accepted
    (validation is done server-side).
    """
    provider_lower = provider.lower()

    if provider_lower in _PI_AI_PROVIDERS:
        return True

    if provider_lower in ("ollama", "openrouter"):
        return True

    if provider_lower not in VALID_MODELS:
        return True

    return model in VALID_MODELS[provider_lower]

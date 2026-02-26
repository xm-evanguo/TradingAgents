from typing import Optional

from .base_client import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .pi_ai_client import PiAiClient


# Providers routed through pi-ai-server
_PI_AI_PROVIDERS = {
    "google-gemini-cli",
    "codex",          # maps to openai-codex in pi-ai
    "openai",
    "google",
    "xai",
    "kimi",           # maps to kimi-coding in pi-ai
}

# Map our provider names → pi-ai provider IDs
_PROVIDER_TO_PI_AI: dict[str, str] = {
    "google-gemini-cli": "google-gemini-cli",
    "codex": "openai-codex",
    "openai": "openai",
    "google": "google",
    "xai": "xai",
    "kimi": "kimi-coding",
}

# Map our provider names → default model ID (when none supplied)
_DEFAULT_MODELS: dict[str, str] = {
    "google-gemini-cli": "gemini-2.5-flash",
    "codex": "gpt-5.2",
}


def create_llm_client(
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    **kwargs,
) -> BaseLLMClient:
    """Create an LLM client for the specified provider.

    Args:
        provider: LLM provider (google-gemini-cli, codex, openai, google, xai,
                  kimi, deepseek, ollama, openrouter, anthropic)
        model: Model name/identifier
        base_url: Optional base URL for API endpoint
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured BaseLLMClient instance

    Raises:
        ValueError: If provider is not supported
    """
    provider_lower = provider.lower()

    # ── pi-ai-server backed providers ────────────────────────────────────────
    if provider_lower in _PI_AI_PROVIDERS:
        pi_provider = _PROVIDER_TO_PI_AI[provider_lower]
        model_id = model or _DEFAULT_MODELS.get(provider_lower, model)
        return _PiAiClientAdapter(
            model_id,
            PiAiClient(
                provider_id=pi_provider,
                model_id=model_id,
                temperature=kwargs.get("temperature"),
                max_tokens=kwargs.get("max_output_tokens"),
                reasoning=kwargs.get("thinking_level"),
            ),
        )

    # ── Direct API providers ─────────────────────────────────────────────────
    if provider_lower in ("deepseek", "ollama", "openrouter"):
        return OpenAIClient(model, base_url, provider=provider_lower, **kwargs)

    if provider_lower == "anthropic":
        return AnthropicClient(model, base_url, **kwargs)

    raise ValueError(f"Unsupported LLM provider: {provider}")


class _PiAiClientAdapter(BaseLLMClient):
    """Adapter to make PiAiClient compatible with the BaseLLMClient interface."""

    def __init__(self, model: str, pi_ai_client: PiAiClient):
        super().__init__(model)
        self._pi_ai_client = pi_ai_client

    def get_llm(self):
        return self._pi_ai_client

    def validate_model(self) -> bool:
        return True

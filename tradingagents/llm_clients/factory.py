from typing import Optional

from .base_client import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .google_client import GoogleClient


def create_llm_client(
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    **kwargs,
) -> BaseLLMClient:
    """Create an LLM client for the specified provider.

    Args:
        provider: LLM provider (openai, anthropic, google, xai, ollama,
                  openrouter, gemini-cli, codex)
        model: Model name/identifier
        base_url: Optional base URL for API endpoint
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured BaseLLMClient instance

    Raises:
        ValueError: If provider is not supported
    """
    provider_lower = provider.lower()

    if provider_lower in ("openai", "ollama", "openrouter", "kimi", "deepseek"):
        return OpenAIClient(model, base_url, provider=provider_lower, **kwargs)

    if provider_lower == "xai":
        return OpenAIClient(model, base_url, provider="xai", **kwargs)

    if provider_lower == "codex":
        from .oauth_utils import get_codex_access_token

        token = get_codex_access_token()
        kwargs["api_key"] = token
        return OpenAIClient(model, base_url, provider="codex", **kwargs)

    if provider_lower == "anthropic":
        return AnthropicClient(model, base_url, **kwargs)

    if provider_lower == "google":
        return GoogleClient(model, base_url, **kwargs)

    if provider_lower == "gemini-cli":
        from .oauth_utils import get_gemini_cli_credentials
        from .code_assist_client import ChatCodeAssist

        creds = get_gemini_cli_credentials()
        chat_model = ChatCodeAssist(
            model=model,
            access_token=creds.token,
            temperature=kwargs.get("temperature"),
            max_output_tokens=kwargs.get("max_output_tokens"),
            thinking_budget=kwargs.get("thinking_budget"),
        )
        # Wrap in a BaseLLMClient-compatible adapter
        return _CodeAssistClientAdapter(model, chat_model)

    raise ValueError(f"Unsupported LLM provider: {provider}")


class _CodeAssistClientAdapter(BaseLLMClient):
    """Adapter to make ChatCodeAssist compatible with the BaseLLMClient interface."""

    def __init__(self, model: str, chat_model):
        super().__init__(model)
        self._chat_model = chat_model

    def get_llm(self):
        return self._chat_model

    def validate_model(self) -> bool:
        return True

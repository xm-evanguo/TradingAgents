import os
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic

from .base_client import BaseLLMClient
from .validators import validate_model


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic Claude models."""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "anthropic",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def _resolve_auth(self) -> tuple[Optional[str], Optional[str]]:
        if self.provider == "minimax":
            api_url = (
                self.base_url
                or os.getenv("MINIMAX_ANTHROPIC_BASE_URL")
                or "https://api.minimax.io/anthropic"
            )
            api_key = os.getenv("MINIMAX_API_KEY")
            return api_url, api_key

        api_url = self.base_url or os.getenv("ANTHROPIC_BASE_URL")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        return api_url, api_key

    def get_llm(self) -> Any:
        """Return configured ChatAnthropic instance."""
        llm_kwargs = {"model": self.model}
        api_url, api_key = self._resolve_auth()
        if api_url:
            llm_kwargs["anthropic_api_url"] = api_url
        if api_key:
            llm_kwargs["anthropic_api_key"] = api_key

        if "timeout" in self.kwargs:
            llm_kwargs["default_request_timeout"] = self.kwargs["timeout"]
        for key in ("max_retries", "max_tokens", "callbacks"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return ChatAnthropic(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Anthropic."""
        if self.provider == "minimax":
            return True
        return validate_model("anthropic", self.model)

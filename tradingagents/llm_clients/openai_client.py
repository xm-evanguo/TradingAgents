import os
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from .base_client import BaseLLMClient
from .validators import validate_model


class UnifiedChatOpenAI(ChatOpenAI):
    """ChatOpenAI subclass that strips incompatible params for certain models."""

    def __init__(self, **kwargs):
        model = kwargs.get("model", "")
        if self._is_reasoning_model(model):
            kwargs.pop("temperature", None)
        super().__init__(**kwargs)

    def _get_request_payload(self, input_, *, stop=None, **kwargs):
        """Intercept the payload to inject empty reasoning_content for kimi if missing."""
        from langchain_core.language_models import LanguageModelInput
        
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        
        if "kimi" in self.model_name.lower():
            # Kimi models with thinking enabled require reasoning_content on assistant messages
            # even when they are just performing tool calls.
            for msg_dict in payload.get("messages", []):
                if msg_dict.get("role") == "assistant" and msg_dict.get("tool_calls"):
                    if "reasoning_content" not in msg_dict or not msg_dict["reasoning_content"]:
                        msg_dict["reasoning_content"] = "Thinking..."
            
            print("\n[DEBUG] Kimi Payload Messages:")
            import json
            with open(".payload.json", "w") as f:
                json.dump(payload.get("messages", []), f, indent=2)
                        
        return payload

    @staticmethod
    def _is_reasoning_model(model: str) -> bool:
        """Check if model is a reasoning model that doesn't support temperature."""
        model_lower = model.lower()
        return (
            model_lower.startswith("o1")
            or model_lower.startswith("o3")
            or "gpt-5" in model_lower
        )


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI, Ollama, OpenRouter, xAI, and Codex OAuth providers."""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> Any:
        """Return configured ChatOpenAI instance."""
        llm_kwargs = {"model": self.model}

        if self.provider == "xai":
            llm_kwargs["base_url"] = "https://api.x.ai/v1"
            api_key = os.environ.get("XAI_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "openrouter":
            llm_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "kimi":
            # The CLI might pass in a broken kimi url, ignore it
            passed_url = self.base_url
            if not passed_url or "api.kimi.ai" in passed_url or "api.moonshot.cn" in passed_url:
                llm_kwargs["base_url"] = "https://api.moonshot.ai/v1"
            else:
                llm_kwargs["base_url"] = passed_url
                
            api_key = os.environ.get("MOONSHOT_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "deepseek":
            llm_kwargs["base_url"] = "https://api.deepseek.com/v1"
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in ("timeout", "max_retries", "reasoning_effort", "api_key", "callbacks"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return UnifiedChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for the provider."""
        return validate_model(self.provider, self.model)

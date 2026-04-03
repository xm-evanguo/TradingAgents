import sys
from typing import Any, Dict, List, Optional, Sequence
import urllib.error

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from .factory import create_llm_client

try:
    from openai import (
        APIConnectionError,
        APITimeoutError,
        APIStatusError,
        AuthenticationError,
        BadRequestError,
        InternalServerError,
        NotFoundError,
        RateLimitError,
    )

    _OPENAI_RETRYABLE_ERRORS = (
        APIConnectionError,
        APITimeoutError,
        APIStatusError,
        AuthenticationError,
        BadRequestError,
        InternalServerError,
        NotFoundError,
        RateLimitError,
    )
except ImportError:  # pragma: no cover - openai is an expected dependency
    _OPENAI_RETRYABLE_ERRORS = ()


_NON_RETRYABLE_ERRORS = (
    AssertionError,
    AttributeError,
    IndexError,
    KeyError,
    NotImplementedError,
    TypeError,
)

_RETRYABLE_TEXT_MARKERS = (
    "api key",
    "authentication",
    "connection",
    "context length",
    "does not exist",
    "invalid api key",
    "invalid model",
    "not found",
    "overloaded",
    "pi-ai-server error",
    "rate limit",
    "service unavailable",
    "timed out",
    "timeout",
    "too many requests",
    "unauthorized",
    "unknown model",
    "unreachable",
    "unsupported model",
    "401",
    "403",
    "404",
    "408",
    "409",
    "429",
    "500",
    "502",
    "503",
    "504",
)


def _candidate_label(candidate: Dict[str, Any]) -> str:
    return f"{candidate['provider']}:{candidate['model']}"


def _message_to_chat_result(message: BaseMessage) -> ChatResult:
    llm_output: Dict[str, Any] = {}
    usage_metadata = getattr(message, "usage_metadata", None)
    if usage_metadata:
        llm_output["token_usage"] = {
            "prompt_tokens": usage_metadata.get("input_tokens", 0),
            "completion_tokens": usage_metadata.get("output_tokens", 0),
            "total_tokens": usage_metadata.get("total_tokens", 0),
        }

    return ChatResult(
        generations=[ChatGeneration(message=message)],
        llm_output=llm_output or None,
    )


def _is_retryable_llm_error(exc: Exception) -> bool:
    if isinstance(exc, _NON_RETRYABLE_ERRORS):
        return False

    retryable_types = (
        TimeoutError,
        ConnectionError,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ) + _OPENAI_RETRYABLE_ERRORS
    if isinstance(exc, retryable_types):
        return True

    module_name = exc.__class__.__module__.lower()
    if module_name.startswith(("openai", "httpx", "urllib", "requests")):
        return True

    text = f"{exc.__class__.__name__}: {exc}".lower()
    return any(marker in text for marker in _RETRYABLE_TEXT_MARKERS)


class FallbackChatModel(BaseChatModel):
    """Retry the same request across an ordered list of provider/model candidates."""

    candidates: List[Dict[str, Any]]
    role: str = "llm"

    _active_index: int = PrivateAttr(default=0)
    _bound_tools: Optional[List[Any]] = PrivateAttr(default=None)
    _candidate_runnables: Dict[int, Any] = PrivateAttr(default_factory=dict)

    @property
    def _llm_type(self) -> str:
        return "fallback-chat-model"

    @property
    def _identifying_params(self) -> dict:
        public_candidates = []
        for candidate in self.candidates:
            public_candidates.append(
                {
                    "provider": candidate["provider"],
                    "model": candidate["model"],
                    "base_url": candidate.get("base_url"),
                }
            )
        return {"role": self.role, "candidates": public_candidates}

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "FallbackChatModel":
        new = self.model_copy(deep=True)
        new._active_index = self._active_index
        new._bound_tools = list(tools)
        new._candidate_runnables = {}
        return new

    def _get_candidate_runnable(self, index: int) -> Any:
        if index not in self._candidate_runnables:
            candidate = self.candidates[index]
            llm_kwargs = dict(candidate.get("llm_kwargs") or {})
            client = create_llm_client(
                provider=candidate["provider"],
                model=candidate["model"],
                base_url=candidate.get("base_url"),
                **llm_kwargs,
            )
            runnable = client.get_llm()
            if self._bound_tools:
                runnable = runnable.bind_tools(self._bound_tools)
            self._candidate_runnables[index] = runnable

        return self._candidate_runnables[index]

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        del run_manager  # Inner model invocations emit their own callbacks.

        last_exc: Optional[Exception] = None
        failure_messages: List[str] = []
        invoke_kwargs = dict(kwargs)
        if stop is not None:
            invoke_kwargs["stop"] = stop

        for index in range(self._active_index, len(self.candidates)):
            candidate = self.candidates[index]
            candidate_label = _candidate_label(candidate)

            try:
                runnable = self._get_candidate_runnable(index)
                message = runnable.invoke(messages, **invoke_kwargs)
                if not isinstance(message, BaseMessage):
                    raise TypeError(
                        f"Expected BaseMessage from {candidate_label}, got {type(message)!r}"
                    )
                self._active_index = index
                return _message_to_chat_result(message)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                failure_messages.append(f"{candidate_label} -> {exc}")
                has_next_candidate = index + 1 < len(self.candidates)
                if not has_next_candidate or not _is_retryable_llm_error(exc):
                    break

                next_label = _candidate_label(self.candidates[index + 1])
                print(
                    f"[TradingAgents] {self.role} LLM request failed on {candidate_label}: {exc}. "
                    f"Retrying with {next_label}.",
                    file=sys.stderr,
                )

        detail = " | ".join(failure_messages)
        raise RuntimeError(
            f"All {self.role} LLM candidates failed. Attempts: {detail}"
        ) from last_exc

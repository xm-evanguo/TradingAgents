"""LangChain ChatModel wrapper for the pi-ai-server local HTTP service.

pi-ai-server (from https://github.com/xm-evanguo/pi-mono) is a lightweight
local HTTP server that exposes a unified LLM API with built-in OAuth and
API-key support.  This client talks to it via plain HTTP so TradingAgents
doesn't need provider-specific SDKs (except for DeepSeek, which pi-ai
doesn't support and is kept on the direct OpenAI-compat path).

For local development, TradingAgents can auto-start pi-ai-server when
PI_AI_SERVER_CMD (or default pi-mono paths) is configured. You can also
start it manually and point PI_AI_SERVER_URL to the running instance.

For OAuth providers (google-gemini-cli, openai-codex) the client fetches a
fresh token from /auth/token on every call; pi-ai-server handles refresh.
For API-key providers (openai, google, xai, kimi-coding) pass the key via
options.apiKey (read from env here).
"""

import json
import os
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional, Sequence
import urllib.request
import urllib.error

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from .pi_ai_server_manager import (
    DEFAULT_PI_AI_SERVER_URL,
    ensure_pi_ai_server_ready,
    get_oauth_token_or_raise,
)

# ── Default server URL (override with PI_AI_SERVER_URL env var) ───────────────
_DEFAULT_SERVER_URL = DEFAULT_PI_AI_SERVER_URL

# ── OAuth providers whose token must be fetched from /auth/token ──────────────
_OAUTH_PROVIDERS = {"google-gemini-cli", "openai-codex"}

# ── API-key providers and the env-var that holds their key ────────────────────
_APIKEY_ENV: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
    "kimi-coding": "MOONSHOT_API_KEY",
}

# ── pi-ai model descriptors keyed by (provider_id, model_id) ─────────────────
# The /complete endpoint needs a full Model object with api/provider/baseUrl.
# We hard-code the fields that pi-ai requires; cost/context are informational.
_MODEL_SPECS: Dict[str, Dict[str, Any]] = {
    "google-gemini-cli": {
        "api": "google-gemini-cli",
        "provider": "google-gemini-cli",
        "baseUrl": "",
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 1000000,
        "maxTokens": 65536,
    },
    "openai-codex": {
        "api": "openai-codex-responses",
        "provider": "openai-codex",
        "baseUrl": "https://api.openai.com/v1",
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 1000000,
        "maxTokens": 32768,
    },
    "openai": {
        "api": "openai-responses",
        "provider": "openai",
        "baseUrl": "https://api.openai.com/v1",
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 128000,
        "maxTokens": 16384,
    },
    "google": {
        "api": "google-generative-ai",
        "provider": "google",
        "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 1000000,
        "maxTokens": 65536,
    },
    "xai": {
        "api": "openai-completions",
        "provider": "xai",
        "baseUrl": "https://api.x.ai/v1",
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 131072,
        "maxTokens": 32768,
    },
    "kimi-coding": {
        "api": "openai-completions",
        "provider": "kimi-coding",
        "baseUrl": "https://api.moonshot.ai/v1",
        "reasoning": False,
        "input": ["text"],
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "contextWindow": 128000,
        "maxTokens": 32768,
    },
}


def _http_post(url: str, payload: dict) -> dict:
    """POST JSON to url and return parsed JSON response."""
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            err_body = json.loads(body_bytes)
            raise RuntimeError(
                f"pi-ai-server error {e.code}: {err_body.get('error', body_bytes.decode())}"
            ) from e
        except (json.JSONDecodeError, AttributeError):
            raise RuntimeError(f"pi-ai-server error {e.code}: {body_bytes.decode()}") from e


def _get_oauth_token(provider_id: str, server_url: str) -> str:
    """Fetch a valid OAuth token from pi-ai-server /auth/token."""
    return get_oauth_token_or_raise(provider_id, server_url)


def _convert_tool_to_pi_ai(tool: BaseTool) -> dict:
    """Convert a LangChain BaseTool to a pi-ai Tool (TypeBox schema subset)."""
    schema = tool.args_schema.schema() if tool.args_schema else {}
    return {
        "name": tool.name,
        "description": tool.description or "",
        "parameters": schema,
    }


def _langchain_messages_to_pi_ai(messages: List[BaseMessage]) -> tuple[Optional[str], List[dict]]:
    """Convert LangChain messages to (systemPrompt, pi-ai messages list)."""
    system_prompt: Optional[str] = None
    pi_messages: List[dict] = []
    ts = int(time.time() * 1000)

    for msg in messages:
        if isinstance(msg, SystemMessage):
            # pi-ai passes system via systemPrompt field, not as a message
            system_prompt = str(msg.content)
        elif isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                pi_messages.append({"role": "user", "content": content, "timestamp": ts})
            else:
                # List of content parts (text only for now)
                text_parts = [
                    {"type": "text", "text": p.get("text", "")}
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                pi_messages.append({"role": "user", "content": text_parts, "timestamp": ts})
        elif isinstance(msg, AIMessage):
            parts = []
            # Text content
            if msg.content:
                parts.append({"type": "text", "text": str(msg.content)})
            # Tool calls → pi-ai ToolCall parts
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    parts.append({
                        "type": "toolCall",
                        "id": tc.get("id", str(uuid.uuid4())),
                        "name": tc["name"],
                        "arguments": tc.get("args", {}),
                    })
            pi_messages.append({
                "role": "assistant",
                "content": parts,
                # These fields are required by pi-ai AssistantMessage but we
                # use placeholder values for history messages since pi-ai only
                # validates the final message schema, not history entries.
                "api": "unknown",
                "provider": "unknown",
                "model": "unknown",
                "usage": {
                    "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
                    "totalTokens": 0,
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
                },
                "stopReason": "stop",
                "timestamp": ts,
            })
        elif isinstance(msg, ToolMessage):
            # pi-ai ToolResultMessage
            content_text = str(msg.content) if msg.content else ""
            pi_messages.append({
                "role": "toolResult",
                "toolCallId": msg.tool_call_id,
                "toolName": msg.name or msg.tool_call_id,
                "content": [{"type": "text", "text": content_text}],
                "isError": False,
                "timestamp": ts,
            })
        else:
            pi_messages.append({
                "role": "user",
                "content": str(msg.content),
                "timestamp": ts,
            })

    return system_prompt, pi_messages


class PiAiClient(BaseChatModel):
    """LangChain ChatModel that calls the pi-ai-server local HTTP service.

    Supports OAuth providers (google-gemini-cli, openai-codex) and
    API-key providers (openai, google, xai, kimi-coding).
    """

    provider_id: str
    """pi-ai provider ID, e.g. 'google-gemini-cli', 'openai', 'xai'."""

    model_id: str
    """Model ID within the provider, e.g. 'gemini-2.5-flash', 'gpt-5-mini'."""

    server_url: str = _DEFAULT_SERVER_URL
    """Base URL of the pi-ai-server (default: http://127.0.0.1:3456)."""

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    reasoning: Optional[str] = None
    """Thinking level: 'minimal', 'low', 'medium', 'high', 'xhigh'."""

    # Tool calling support (populated by bind_tools)
    _bound_tools: Optional[List[dict]] = None

    @property
    def _llm_type(self) -> str:
        return "pi-ai"

    @property
    def _identifying_params(self) -> dict:
        return {"provider_id": self.provider_id, "model_id": self.model_id}

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "PiAiClient":
        """Bind LangChain tools for function-calling."""
        pi_tools = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                pi_tools.append(_convert_tool_to_pi_ai(tool))
            elif isinstance(tool, dict):
                pi_tools.append(tool)
            else:
                raise ValueError(f"Unsupported tool type: {type(tool)}")
        new = self.model_copy()
        new._bound_tools = pi_tools
        return new

    def _get_api_key(self) -> Optional[str]:
        """Return the API key to pass in options (None for OAuth providers)."""
        if self.provider_id in _OAUTH_PROVIDERS:
            return _get_oauth_token(self.provider_id, self.server_url)
        env_var = _APIKEY_ENV.get(self.provider_id)
        if env_var:
            return os.environ.get(env_var)
        return None

    def _build_model_spec(self) -> dict:
        """Build the pi-ai Model object for the current provider/model."""
        spec = dict(_MODEL_SPECS.get(self.provider_id, {
            "api": "openai-completions",
            "provider": self.provider_id,
            "baseUrl": "",
            "reasoning": False,
            "input": ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 128000,
            "maxTokens": 16384,
        }))
        spec["id"] = self.model_id
        spec["name"] = self.model_id
        return spec

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not ensure_pi_ai_server_ready(self.server_url):
            raise RuntimeError(
                f"pi-ai-server is unreachable at '{self.server_url}'. "
                "Set PI_AI_SERVER_CMD/PI_AI_SERVER_CWD for auto-start, or set "
                "PI_AI_SERVER_URL to a running server."
            )

        system_prompt, pi_messages = _langchain_messages_to_pi_ai(messages)

        context: Dict[str, Any] = {"messages": pi_messages}
        if system_prompt:
            context["systemPrompt"] = system_prompt
        if self._bound_tools:
            context["tools"] = self._bound_tools

        options: Dict[str, Any] = {}
        api_key = self._get_api_key()
        if api_key:
            options["apiKey"] = api_key
        if self.temperature is not None:
            options["temperature"] = self.temperature
        if self.max_tokens is not None:
            options["maxTokens"] = self.max_tokens
        if self.reasoning is not None:
            options["reasoning"] = self.reasoning

        payload = {
            "model": self._build_model_spec(),
            "context": context,
            "options": options,
        }

        response = _http_post(f"{self.server_url}/complete", payload)

        return self._parse_response(response)

    def _parse_response(self, response: dict) -> ChatResult:
        """Parse an AssistantMessage from pi-ai-server into a LangChain ChatResult."""
        content_parts = response.get("content", [])

        text_parts: List[str] = []
        tool_calls: List[dict] = []

        for part in content_parts:
            part_type = part.get("type")
            if part_type == "text":
                text = part.get("text", "")
                if text:
                    text_parts.append(text)
            elif part_type == "thinking":
                # Ignore thinking blocks (don't surface to LangChain)
                pass
            elif part_type == "toolCall":
                tool_calls.append({
                    "name": part["name"],
                    "args": part.get("arguments", {}),
                    "id": part.get("id", str(uuid.uuid4())),
                    "type": "tool_call",
                })

        text = "\n".join(text_parts)
        ai_message = AIMessage(
            content=text,
            tool_calls=tool_calls,
        )

        # Token usage
        usage = response.get("usage", {})
        llm_output: Dict[str, Any] = {}
        if usage:
            llm_output["token_usage"] = {
                "prompt_tokens": usage.get("input", 0),
                "completion_tokens": usage.get("output", 0),
                "total_tokens": usage.get("totalTokens", 0),
            }

        return ChatResult(
            generations=[ChatGeneration(message=ai_message)],
            llm_output=llm_output,
        )

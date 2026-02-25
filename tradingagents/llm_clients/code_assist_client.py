"""LangChain ChatModel wrapper for the Google Code Assist API.

This allows using the Gemini CLI's OAuth credentials to call Gemini models
via the Code Assist API endpoint (cloudcode-pa.googleapis.com), which is
the same API the Gemini CLI uses internally.
"""

import json
import os
import uuid
from typing import Any, Dict, List, Optional, Sequence

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


CODE_ASSIST_ENDPOINT = "https://cloudcode-pa.googleapis.com"
CODE_ASSIST_API_VERSION = "v1internal"


def _convert_tool_to_function_declaration(tool: BaseTool) -> dict:
    """Convert a LangChain tool to a Gemini function declaration."""
    schema = tool.args_schema.schema() if tool.args_schema else {}
    # Build parameters from JSON schema
    parameters = {}
    if schema.get("properties"):
        parameters["type"] = "OBJECT"
        parameters["properties"] = {}
        for name, prop in schema["properties"].items():
            param = {}
            json_type = prop.get("type", "string")
            type_map = {
                "string": "STRING",
                "integer": "INTEGER",
                "number": "NUMBER",
                "boolean": "BOOLEAN",
                "array": "ARRAY",
                "object": "OBJECT",
            }
            param["type"] = type_map.get(json_type, "STRING")
            if "description" in prop:
                param["description"] = prop["description"]
            if "enum" in prop:
                param["enum"] = prop["enum"]
            parameters["properties"][name] = param
        if schema.get("required"):
            parameters["required"] = schema["required"]

    decl = {
        "name": tool.name,
        "description": tool.description or "",
    }
    if parameters:
        decl["parameters"] = parameters
    return decl


class ChatCodeAssist(BaseChatModel):
    """Chat model that uses the Google Code Assist API (Gemini CLI backend).

    This calls the same API that 'gemini' CLI uses, authenticating via OAuth.
    """

    model: str
    """Gemini model name (e.g. 'gemini-2.5-flash')."""

    access_token: str
    """OAuth access token from Gemini CLI."""

    project_id: Optional[str] = None
    """Cloud AI Companion project ID (auto-discovered if not set)."""

    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    thinking_budget: Optional[int] = None

    # Tool calling support (set via bind_tools)
    _bound_tools: Optional[List[dict]] = None

    @property
    def _llm_type(self) -> str:
        return "code-assist"

    @property
    def _identifying_params(self) -> dict:
        return {"model": self.model}

    def bind_tools(
        self,
        tools: Sequence[Any],
        **kwargs: Any,
    ) -> "ChatCodeAssist":
        """Bind tools to the model for function calling."""
        tool_declarations = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                tool_declarations.append(
                    _convert_tool_to_function_declaration(tool)
                )
            elif isinstance(tool, dict):
                tool_declarations.append(tool)
            else:
                raise ValueError(f"Unsupported tool type: {type(tool)}")

        # Create a copy with tools bound
        new = self.model_copy()
        new._bound_tools = tool_declarations
        return new

    def _setup_project(self) -> str:
        """Get the Code Assist project ID via the loadCodeAssist API."""
        if self.project_id:
            return self.project_id

        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get(
            "GOOGLE_CLOUD_PROJECT_ID"
        )

        import urllib.request

        url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:loadCodeAssist"
        body = json.dumps(
            {
                "cloudaicompanionProject": project,
                "metadata": {
                    "ideType": "IDE_UNSPECIFIED",
                    "platform": "PLATFORM_UNSPECIFIED",
                    "pluginType": "GEMINI",
                    "duetProject": project,
                },
            }
        ).encode()

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        resp_project = data.get("cloudaicompanionProject")
        if resp_project:
            self.project_id = resp_project
        elif project:
            self.project_id = project
        else:
            self.project_id = ""

        return self.project_id

    def _call_api(self, request_body: dict) -> dict:
        """Call the Code Assist generateContent API."""
        import urllib.request

        if not self.project_id:
            self._setup_project()

        url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:generateContent"
        body = json.dumps(
            {
                "model": self.model,
                "project": self.project_id,
                "user_prompt_id": str(uuid.uuid4()),
                "request": request_body,
            }
        ).encode()

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def _messages_to_contents(
        self, messages: List[BaseMessage]
    ) -> tuple[Optional[dict], list[dict]]:
        """Convert LangChain messages to Code Assist content format."""
        system_instruction = None
        contents = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_instruction = {
                    "parts": [{"text": msg.content}],
                }
            elif isinstance(msg, HumanMessage):
                contents.append(
                    {"role": "user", "parts": [{"text": msg.content}]}
                )
            elif isinstance(msg, AIMessage):
                parts = []
                if msg.content:
                    parts.append({"text": msg.content})
                # Include tool calls as functionCall parts
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append(
                            {
                                "functionCall": {
                                    "name": tc["name"],
                                    "args": tc["args"],
                                }
                            }
                        )
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif isinstance(msg, ToolMessage):
                # Tool results → functionResponse
                # Try to parse content as JSON, fall back to string
                try:
                    result = json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    result = {"result": msg.content}
                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": msg.name or msg.tool_call_id,
                                    "response": result,
                                }
                            }
                        ],
                    }
                )
            else:
                contents.append(
                    {"role": "user", "parts": [{"text": str(msg.content)}]}
                )

        return system_instruction, contents

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_instruction, contents = self._messages_to_contents(messages)

        generation_config: Dict[str, Any] = {}
        if self.temperature is not None:
            generation_config["temperature"] = self.temperature
        if self.max_output_tokens is not None:
            generation_config["maxOutputTokens"] = self.max_output_tokens
        if stop:
            generation_config["stopSequences"] = stop
        if self.thinking_budget is not None:
            generation_config["thinkingConfig"] = {
                "thinkingBudget": self.thinking_budget
            }

        request_body: Dict[str, Any] = {"contents": contents}
        if system_instruction:
            request_body["systemInstruction"] = system_instruction
        if generation_config:
            request_body["generationConfig"] = generation_config

        # Add tools if bound
        if self._bound_tools:
            request_body["tools"] = [
                {"functionDeclarations": self._bound_tools}
            ]

        response = self._call_api(request_body)

        # Parse response
        inner = response.get("response", response)
        candidates = inner.get("candidates", [])
        if not candidates:
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=""))]
            )

        parts = candidates[0].get("content", {}).get("parts", [])

        # Extract text and tool calls
        text_parts = []
        tool_calls = []
        for part in parts:
            if "text" in part:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    {
                        "name": fc["name"],
                        "args": fc.get("args", {}),
                        "id": str(uuid.uuid4()),
                        "type": "tool_call",
                    }
                )

        text = "".join(text_parts)

        # Build AIMessage with tool_calls if present
        ai_message = AIMessage(
            content=text,
            tool_calls=tool_calls if tool_calls else [],
        )

        # Extract usage metadata
        usage = inner.get("usageMetadata", {})
        llm_output: Dict[str, Any] = {}
        if usage:
            llm_output["token_usage"] = {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            }

        return ChatResult(
            generations=[ChatGeneration(message=ai_message)],
            llm_output=llm_output,
        )

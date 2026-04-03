import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from tradingagents.llm_clients.fallback_chat_model import FallbackChatModel


class FakeClient:
    def __init__(self, llm):
        self._llm = llm

    def get_llm(self):
        return self._llm


class FakeRunnable:
    def __init__(self, parent):
        self.parent = parent

    def invoke(self, messages, **kwargs):
        return self.parent.invoke(messages, **kwargs)


class FakeLLM:
    def __init__(self, name, outcomes):
        self.name = name
        self.outcomes = list(outcomes)
        self.calls = 0
        self.bound_tools = []

    def invoke(self, messages, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def bind_tools(self, tools):
        self.bound_tools.append(list(tools))
        return FakeRunnable(self)


class RuntimeFallbackTest(unittest.TestCase):
    def test_request_failure_retries_next_candidate_and_sticks_to_successful_route(self) -> None:
        primary = FakeLLM(
            "codex",
            [RuntimeError("pi-ai-server error 503: unavailable")],
        )
        fallback = FakeLLM(
            "gemini",
            [
                AIMessage(content="first success"),
                AIMessage(content="second success"),
            ],
        )

        def fake_create_llm_client(provider, model, base_url=None, **kwargs):
            mapping = {
                ("codex", "gpt-5.4"): primary,
                ("google-gemini-cli", "gemini-3.1-pro-preview"): fallback,
            }
            return FakeClient(mapping[(provider, model)])

        with patch(
            "tradingagents.llm_clients.fallback_chat_model.create_llm_client",
            side_effect=fake_create_llm_client,
        ):
            llm = FallbackChatModel(
                role="deep",
                candidates=[
                    {"provider": "codex", "model": "gpt-5.4", "base_url": ""},
                    {
                        "provider": "google-gemini-cli",
                        "model": "gemini-3.1-pro-preview",
                        "base_url": "",
                    },
                ],
            )

            first = llm.invoke([HumanMessage(content="hello")])
            second = llm.invoke([HumanMessage(content="again")])

        self.assertEqual(first.content, "first success")
        self.assertEqual(second.content, "second success")
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 2)

    def test_bind_tools_uses_same_runtime_fallback_chain(self) -> None:
        primary = FakeLLM(
            "codex",
            [RuntimeError("pi-ai-server error 429: rate limit")],
        )
        fallback = FakeLLM(
            "gemini",
            [AIMessage(content="", tool_calls=[{"name": "lookup", "args": {}, "id": "1", "type": "tool_call"}])],
        )

        def fake_create_llm_client(provider, model, base_url=None, **kwargs):
            mapping = {
                ("codex", "gpt-5.4"): primary,
                ("google-gemini-cli", "gemini-3.1-pro-preview"): fallback,
            }
            return FakeClient(mapping[(provider, model)])

        with patch(
            "tradingagents.llm_clients.fallback_chat_model.create_llm_client",
            side_effect=fake_create_llm_client,
        ):
            llm = FallbackChatModel(
                role="deep",
                candidates=[
                    {"provider": "codex", "model": "gpt-5.4", "base_url": ""},
                    {
                        "provider": "google-gemini-cli",
                        "model": "gemini-3.1-pro-preview",
                        "base_url": "",
                    },
                ],
            ).bind_tools(["lookup-tool"])

            result = llm.invoke([HumanMessage(content="use tool")])

        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 1)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(primary.bound_tools, [["lookup-tool"]])
        self.assertEqual(fallback.bound_tools, [["lookup-tool"]])


if __name__ == "__main__":
    unittest.main()

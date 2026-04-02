import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import HumanMessage

from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.model_router import (
    DEFAULT_CODEX_MODEL,
    GEMINI_QUICK_MODEL,
    resolve_llm_plan,
)
from tradingagents.llm_clients.pi_ai_client import PiAiClient
from tradingagents.llm_clients import pi_ai_server_manager


class ModelRoutingDefaultsTest(unittest.TestCase):
    def test_codex_deep_prefers_gemini_quick_when_gemini_auth_exists(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[True, True],
        ):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "codex")
        self.assertEqual(plan["quick_provider"], "google-gemini-cli")
        self.assertEqual(plan["deep_model"], DEFAULT_CODEX_MODEL)
        self.assertEqual(plan["quick_model"], GEMINI_QUICK_MODEL)

    def test_codex_deep_falls_back_to_api_key_quick_without_gemini_auth(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[True, False],
        ), patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}, clear=True):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "codex")
        self.assertEqual(plan["deep_model"], DEFAULT_CODEX_MODEL)
        self.assertEqual(plan["quick_provider"], "deepseek")
        self.assertEqual(plan["quick_model"], "deepseek-chat")

    def test_gemini_auth_handles_both_roles_when_codex_is_unavailable(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[False, True],
        ):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "google-gemini-cli")
        self.assertEqual(plan["deep_model"], "gemini-3.1-pro-preview")
        self.assertEqual(plan["quick_provider"], "google-gemini-cli")
        self.assertEqual(plan["quick_model"], GEMINI_QUICK_MODEL)

    def test_codex_factory_default_model_matches_router_default(self) -> None:
        client = create_llm_client("codex", "")

        self.assertEqual(client.model, DEFAULT_CODEX_MODEL)

    def test_api_key_priority_prefers_kimi_over_deepseek(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[False, False],
        ), patch.dict(
            "os.environ",
            {"MOONSHOT_API_KEY": "kimi-key", "DEEPSEEK_API_KEY": "deepseek-key"},
            clear=True,
        ):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "kimi")
        self.assertEqual(plan["deep_model"], "kimi-k2.5")
        self.assertEqual(plan["quick_provider"], "kimi")
        self.assertEqual(plan["quick_model"], "kimi-k2.5")

    def test_api_key_priority_prefers_minimax_over_kimi(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[False, False],
        ), patch.dict(
            "os.environ",
            {"MINIMAX_API_KEY": "minimax-key", "MOONSHOT_API_KEY": "kimi-key"},
            clear=True,
        ):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "minimax")
        self.assertEqual(plan["deep_model"], "MiniMax-M2.7")
        self.assertEqual(plan["quick_provider"], "minimax")
        self.assertEqual(plan["quick_model"], "MiniMax-M2.7-highspeed")

    def test_api_key_priority_uses_minimax_before_deepseek(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[False, False],
        ), patch.dict(
            "os.environ",
            {"MINIMAX_API_KEY": "minimax-key", "DEEPSEEK_API_KEY": "deepseek-key"},
            clear=True,
        ):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "minimax")
        self.assertEqual(plan["deep_model"], "MiniMax-M2.7")
        self.assertEqual(plan["quick_provider"], "minimax")
        self.assertEqual(plan["quick_model"], "MiniMax-M2.7-highspeed")

    def test_factory_supports_minimax_direct_provider(self) -> None:
        client = create_llm_client("minimax", "MiniMax-M2.7")

        self.assertEqual(client.provider, "minimax")
        self.assertEqual(client.model, "MiniMax-M2.7")

    def test_codex_pi_ai_spec_uses_chatgpt_backend(self) -> None:
        client = PiAiClient(provider_id="openai-codex", model_id=DEFAULT_CODEX_MODEL)

        self.assertEqual(
            client._build_model_spec()["baseUrl"],
            "https://chatgpt.com/backend-api",
        )

    def test_default_start_spec_falls_back_to_compat_server(self) -> None:
        compat_server = (
            Path(pi_ai_server_manager.__file__).resolve().parents[2]
            / "scripts/pi_ai_server_compat.mjs"
        )

        def fake_exists(path: Path) -> bool:
            return path == compat_server

        with patch("pathlib.Path.exists", autospec=True, side_effect=fake_exists):
            start_spec = pi_ai_server_manager._default_start_spec()

        self.assertEqual(
            start_spec,
            (["node", str(compat_server)], str(compat_server.parent.parent)),
        )

    def test_codex_generate_adds_default_system_prompt_when_missing(self) -> None:
        client = PiAiClient(provider_id="openai-codex", model_id=DEFAULT_CODEX_MODEL)

        with patch(
            "tradingagents.llm_clients.pi_ai_client.ensure_pi_ai_server_ready",
            return_value=True,
        ), patch.object(client, "_get_api_key", return_value="token"), patch(
            "tradingagents.llm_clients.pi_ai_client._http_post",
            return_value={"content": [{"type": "text", "text": "ok"}]},
        ) as mock_post:
            client._generate([HumanMessage(content="hello")])

        payload = mock_post.call_args.args[1]
        self.assertEqual(
            payload["context"]["systemPrompt"],
            "You are a helpful assistant.",
        )

    def test_kimi_coding_provider_is_rejected(self) -> None:
        client = PiAiClient(provider_id="kimi-coding", model_id="kimi-k2.5")

        with self.assertRaisesRegex(ValueError, "reserved for Claude Code"):
            client._build_model_spec()


if __name__ == "__main__":
    unittest.main()

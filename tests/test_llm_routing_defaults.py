import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import HumanMessage

from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.model_router import (
    DEFAULT_CODEX_MODEL,
    resolve_llm_plan,
)
from tradingagents.llm_clients.pi_ai_client import PiAiClient
from tradingagents.llm_clients import pi_ai_server_manager


class ModelRoutingDefaultsTest(unittest.TestCase):
    def test_codex_oauth_defaults_to_gpt_5_4(self) -> None:
        with patch(
            "tradingagents.llm_clients.model_router._has_pi_ai_oauth",
            side_effect=[True, False],
        ):
            plan = resolve_llm_plan()

        self.assertEqual(plan["deep_provider"], "codex")
        self.assertEqual(plan["quick_provider"], "codex")
        self.assertEqual(plan["deep_model"], DEFAULT_CODEX_MODEL)
        self.assertEqual(plan["quick_model"], DEFAULT_CODEX_MODEL)

    def test_codex_factory_default_model_matches_router_default(self) -> None:
        client = create_llm_client("codex", "")

        self.assertEqual(client.model, DEFAULT_CODEX_MODEL)

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


if __name__ == "__main__":
    unittest.main()

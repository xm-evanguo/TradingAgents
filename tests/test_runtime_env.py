import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tradingagents import runtime_env


def _write_env_file(path: Path, *lines: str) -> None:
    path.write_text("\n".join([*lines, ""]), encoding="utf-8")


class RuntimeEnvBootstrapTest(unittest.TestCase):
    def setUp(self) -> None:
        runtime_env._BOOTSTRAPPED = False

    def tearDown(self) -> None:
        runtime_env._BOOTSTRAPPED = False

    def test_bootstrap_runtime_env_prefers_doppler_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env"
            _write_env_file(
                env_file,
                "DEEPSEEK_API_KEY=from-dotenv",
                "XAI_API_KEY=dotenv-xai",
                "DOPPLER_PROJECT=openclaw",
                "DOPPLER_CONFIG=dev",
                "DOPPLER_TOKEN=doppler-token-123",
            )

            calls: list[list[str]] = []
            env_store: dict[str, str] = {}

            def fake_runner(
                cmd: list[str], *, check: bool, capture_output: bool, text: bool
            ) -> subprocess.CompletedProcess[str]:
                calls.append(cmd)
                self.assertTrue(check)
                self.assertTrue(capture_output)
                self.assertTrue(text)
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout="DEEPSEEK_API_KEY=from-doppler\nMOONSHOT_API_KEY=moonshot\n",
                    stderr="",
                )

            runtime_env.bootstrap_runtime_env(
                env_file=env_file, environ=env_store, runner=fake_runner
            )

            self.assertEqual(env_store["DEEPSEEK_API_KEY"], "from-doppler")
            self.assertEqual(env_store["MOONSHOT_API_KEY"], "moonshot")
            self.assertEqual(env_store["XAI_API_KEY"], "dotenv-xai")
            self.assertEqual(
                calls,
                [
                    [
                        "doppler",
                        "secrets",
                        "download",
                        "--format=env",
                        "--no-file",
                        "--project",
                        "openclaw",
                        "--config",
                        "dev",
                        "--token",
                        "doppler-token-123",
                    ]
                ],
            )

    def test_bootstrap_runtime_env_keeps_explicit_process_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env"
            _write_env_file(
                env_file,
                "DEEPSEEK_API_KEY=from-dotenv",
                "DOPPLER_PROJECT=openclaw",
                "DOPPLER_CONFIG=dev",
            )

            env_store = {"DEEPSEEK_API_KEY": "from-process"}

            def fake_runner(
                cmd: list[str], *, check: bool, capture_output: bool, text: bool
            ) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout="DEEPSEEK_API_KEY=from-doppler\nMOONSHOT_API_KEY=moonshot\n",
                    stderr="",
                )

            runtime_env.bootstrap_runtime_env(
                env_file=env_file, environ=env_store, runner=fake_runner
            )

            self.assertEqual(env_store["DEEPSEEK_API_KEY"], "from-process")
            self.assertEqual(env_store["MOONSHOT_API_KEY"], "moonshot")

    def test_bootstrap_runtime_env_skips_doppler_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env"
            _write_env_file(
                env_file,
                "DOPPLER_ENABLED=0",
                "DOPPLER_PROJECT=openclaw",
                "DOPPLER_CONFIG=dev",
                "DEEPSEEK_API_KEY=from-dotenv",
            )

            env_store: dict[str, str] = {}

            def fake_runner(
                cmd: list[str], *, check: bool, capture_output: bool, text: bool
            ) -> subprocess.CompletedProcess[str]:
                raise AssertionError("Doppler should not run when DOPPLER_ENABLED=0")

            runtime_env.bootstrap_runtime_env(
                env_file=env_file, environ=env_store, runner=fake_runner
            )

            self.assertEqual(env_store["DEEPSEEK_API_KEY"], "from-dotenv")

    def test_load_doppler_secrets_raises_clear_error_when_cli_fails(self) -> None:
        def fake_runner(
            cmd: list[str], *, check: bool, capture_output: bool, text: bool
        ) -> subprocess.CompletedProcess[str]:
            raise subprocess.CalledProcessError(1, cmd, stderr="forbidden")

        with self.assertRaises(RuntimeError) as exc_info:
            runtime_env._load_doppler_secrets(
                {
                    "DOPPLER_PROJECT": "openclaw",
                    "DOPPLER_CONFIG": "dev",
                    "DOPPLER_TOKEN": "doppler-token-123",
                },
                runner=fake_runner,
            )

        self.assertIn("forbidden", str(exc_info.exception))

    def test_load_doppler_secrets_skips_when_binary_missing_and_no_token(self) -> None:
        with patch.object(runtime_env.shutil, "which", return_value=None):
            result = runtime_env._load_doppler_secrets(
                {
                    "DOPPLER_PROJECT": "openclaw",
                    "DOPPLER_CONFIG": "dev",
                }
            )

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()

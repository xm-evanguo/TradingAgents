from collections.abc import Mapping
from io import StringIO
from pathlib import Path
import os
import shutil
import subprocess

from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = ROOT_DIR / ".env"
FALSE_VALUES = {"0", "false", "no", "off"}

_BOOTSTRAPPED = False


def _string_env_values(values: Mapping[str, str | None]) -> dict[str, str]:
    return {key: value for key, value in values.items() if isinstance(value, str)}


def _read_dotenv_file(env_file: Path) -> dict[str, str]:
    if not env_file.exists():
        return {}
    return _string_env_values(dotenv_values(env_file))


def _is_loader_enabled(env_map: Mapping[str, str], prefix: str) -> bool:
    raw_enabled = env_map.get(f"{prefix}_ENABLED", "true").strip().lower()
    return raw_enabled not in FALSE_VALUES


def _load_doppler_secrets(
    env_map: Mapping[str, str],
    *,
    runner: callable = subprocess.run,
) -> dict[str, str]:
    token = env_map.get("DOPPLER_TOKEN")
    project = env_map.get("DOPPLER_PROJECT")
    config = env_map.get("DOPPLER_CONFIG")
    if not _is_loader_enabled(env_map, "DOPPLER"):
        return {}

    if not (token or project or config):
        return {}

    doppler_binary = "doppler"
    if runner is subprocess.run and not shutil.which(doppler_binary):
        if token:
            raise RuntimeError(
                "DOPPLER_TOKEN is set but the doppler CLI is not installed."
            )
        return {}

    cmd = [
        doppler_binary,
        "secrets",
        "download",
        "--format=env",
        "--no-file",
    ]
    if project:
        cmd.extend(["--project", project])
    if config:
        cmd.extend(["--config", config])
    if token:
        cmd.extend(["--token", token])

    try:
        result = runner(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "DOPPLER_TOKEN or DOPPLER_* is set but the doppler CLI is not installed."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"Failed to download secrets from Doppler: {stderr}") from exc

    return _string_env_values(dotenv_values(stream=StringIO(result.stdout)))


def bootstrap_runtime_env(
    *,
    env_file: Path = DEFAULT_ENV_FILE,
    environ: dict[str, str] | None = None,
    runner: callable = subprocess.run,
) -> None:
    global _BOOTSTRAPPED

    if _BOOTSTRAPPED:
        return

    env_store = environ if environ is not None else os.environ
    original_env_keys = set(env_store.keys())

    for key, value in _read_dotenv_file(env_file).items():
        env_store.setdefault(key, value)

    protected_keys = set(original_env_keys)
    for key, value in _load_doppler_secrets(env_store, runner=runner).items():
        if key in protected_keys:
            continue
        env_store[key] = value
        protected_keys.add(key)

    _BOOTSTRAPPED = True

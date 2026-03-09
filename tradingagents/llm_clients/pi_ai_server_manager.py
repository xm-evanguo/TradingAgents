import json
import os
import shlex
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Optional, Sequence, Tuple


DEFAULT_PI_AI_SERVER_URL = "http://127.0.0.1:3456"
AUTH_TIMEOUT_SECONDS = 3
_STARTUP_WAIT_SECONDS = 8.0
_POLL_INTERVAL_SECONDS = 0.25

_STATE_LOCK = Lock()
_SERVER_START_ATTEMPTED = False
_SERVER_PROCESS: Optional[subprocess.Popen] = None


def _is_local_server_url(server_url: str) -> bool:
    parsed = urllib.parse.urlparse(server_url)
    host = (parsed.hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def _probe_auth_endpoint(server_url: str) -> bool:
    payload = json.dumps({"providerId": "openai-codex"}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url}/auth/token",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=AUTH_TIMEOUT_SECONDS):
            return True
    except urllib.error.HTTPError as err:
        # 404 means incompatible server. Other HTTP responses mean endpoint exists.
        return err.code != 404
    except urllib.error.URLError:
        return False


def _default_start_spec() -> Optional[Tuple[Sequence[str], Optional[str]]]:
    pi_mono_root = Path(os.path.expanduser(os.getenv("PI_MONO_DIR", "~/code/pi-mono")))
    dist_server = pi_mono_root / "packages/ai-server/dist/server.js"
    if dist_server.exists():
        return ["node", str(dist_server)], str(pi_mono_root)

    src_server = pi_mono_root / "packages/ai-server/src/server.ts"
    if src_server.exists():
        return ["npx", "tsx", "packages/ai-server/src/server.ts"], str(pi_mono_root)

    compat_server = Path(__file__).resolve().parents[2] / "scripts/pi_ai_server_compat.mjs"
    if compat_server.exists():
        return ["node", str(compat_server)], str(compat_server.parent.parent)

    return None


def _resolve_start_spec() -> Optional[Tuple[Sequence[str], Optional[str]]]:
    command_env = (os.getenv("PI_AI_SERVER_CMD") or "").strip()
    if command_env:
        cmd = shlex.split(command_env)
        if not cmd:
            return None
        cwd = (os.getenv("PI_AI_SERVER_CWD") or "").strip() or None
        if cwd:
            cwd = os.path.expanduser(cwd)
        return cmd, cwd
    return _default_start_spec()


def _manual_start_hint() -> str:
    return (
        "Set PI_AI_SERVER_CMD (and optional PI_AI_SERVER_CWD), or start pi-ai-server manually "
        "and set PI_AI_SERVER_URL."
    )


def ensure_pi_ai_server_ready(server_url: str) -> bool:
    if _probe_auth_endpoint(server_url):
        return True
    if not _is_local_server_url(server_url):
        return False

    global _SERVER_START_ATTEMPTED, _SERVER_PROCESS
    with _STATE_LOCK:
        if _probe_auth_endpoint(server_url):
            return True

        if _SERVER_PROCESS is not None and _SERVER_PROCESS.poll() is None:
            # Another call already started it; just wait below.
            pass
        elif _SERVER_START_ATTEMPTED:
            return False
        else:
            start_spec = _resolve_start_spec()
            if not start_spec:
                _SERVER_START_ATTEMPTED = True
                return False

            cmd, cwd = start_spec
            try:
                _SERVER_PROCESS = subprocess.Popen(
                    list(cmd),
                    cwd=cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                _SERVER_START_ATTEMPTED = True
            except OSError:
                _SERVER_START_ATTEMPTED = True
                return False

    deadline = time.time() + _STARTUP_WAIT_SECONDS
    while time.time() < deadline:
        if _probe_auth_endpoint(server_url):
            return True
        if _SERVER_PROCESS is not None and _SERVER_PROCESS.poll() is not None:
            return False
        time.sleep(_POLL_INTERVAL_SECONDS)
    return _probe_auth_endpoint(server_url)


def fetch_oauth_token(provider_id: str, server_url: str) -> Optional[str]:
    if not ensure_pi_ai_server_ready(server_url):
        return None

    payload = json.dumps({"providerId": provider_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url}/auth/token",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=AUTH_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read())
            token = data.get("apiKey")
            return token if isinstance(token, str) and token.strip() else None
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def get_oauth_token_or_raise(provider_id: str, server_url: str) -> str:
    token = fetch_oauth_token(provider_id, server_url)
    if token:
        return token
    if not _probe_auth_endpoint(server_url):
        raise RuntimeError(
            f"pi-ai-server is unreachable at '{server_url}'. {_manual_start_hint()}"
        )
    raise RuntimeError(
        f"No OAuth token returned for provider '{provider_id}'. "
        f"Run pi-ai login for this provider, then retry."
    )

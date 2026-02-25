"""OAuth utilities for reading cached CLI credentials.

Reads tokens from:
- Gemini CLI: ~/.gemini/oauth_creds.json
- Codex CLI:  ~/.codex/auth.json
"""
import os
import json
import time
from pathlib import Path
from typing import Optional

# Gemini CLI OAuth constants (from @google/gemini-cli-core)
_GEMINI_CREDS_PATH = Path.home() / ".gemini" / "oauth_creds.json"
_GEMINI_TOKEN_URI = "https://oauth2.googleapis.com/token"
_GEMINI_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

# Codex CLI OAuth constants
_CODEX_AUTH_PATH = Path.home() / ".codex" / "auth.json"


def get_gemini_cli_credentials():
    """Read Gemini CLI OAuth credentials and return a google.auth Credentials object.

    Reads ~/.gemini/oauth_creds.json, refreshes if expired using the Gemini CLI's
    OAuth client credentials, and returns a google.oauth2.credentials.Credentials.

    Returns:
        google.oauth2.credentials.Credentials

    Raises:
        FileNotFoundError: If ~/.gemini/oauth_creds.json doesn't exist
        RuntimeError: If credentials cannot be refreshed
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from datetime import datetime, timezone

    if not _GEMINI_CREDS_PATH.exists():
        raise FileNotFoundError(
            f"Gemini CLI credentials not found at {_GEMINI_CREDS_PATH}. "
            "Run 'gemini' CLI and log in with your Google account first."
        )

    data = json.loads(_GEMINI_CREDS_PATH.read_text())

    # Build expiry as naive UTC datetime (google.auth uses naive UTC internally)
    expiry_dt = None
    expiry_ms = data.get("expiry_date", 0)
    if expiry_ms:
        expiry_dt = datetime.utcfromtimestamp(expiry_ms / 1000)

    creds = Credentials(
        token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_uri=_GEMINI_TOKEN_URI,
        CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        scopes=_GEMINI_SCOPES,
        expiry=expiry_dt,
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Write refreshed token back to file
            data["access_token"] = creds.token
            if creds.expiry:
                data["expiry_date"] = int(creds.expiry.timestamp() * 1000)
            _GEMINI_CREDS_PATH.write_text(json.dumps(data, indent=2))
        except Exception as e:
            raise RuntimeError(
                f"Failed to refresh Gemini CLI OAuth token: {e}. "
                "Try re-authenticating with the Gemini CLI."
            ) from e

    return creds


def get_codex_access_token() -> str:
    """Read Codex CLI OAuth access token.

    Reads ~/.codex/auth.json and returns the access_token for use as
    an OpenAI API key / bearer token.

    Returns:
        str: The access token

    Raises:
        FileNotFoundError: If ~/.codex/auth.json doesn't exist
        ValueError: If no access token is found
    """
    if not _CODEX_AUTH_PATH.exists():
        raise FileNotFoundError(
            f"Codex CLI credentials not found at {_CODEX_AUTH_PATH}. "
            "Run 'codex login' first."
        )

    data = json.loads(_CODEX_AUTH_PATH.read_text())

    # Codex stores tokens under "tokens" key
    tokens = data.get("tokens", {})
    access_token = tokens.get("access_token")

    if not access_token:
        # Fall back to OPENAI_API_KEY in the file
        access_token = data.get("OPENAI_API_KEY")

    if not access_token:
        raise ValueError(
            "No access token found in Codex CLI auth. "
            "Run 'codex login' to authenticate."
        )

    return access_token


def get_codex_refresh_token() -> Optional[str]:
    """Read Codex CLI refresh token if available."""
    if not _CODEX_AUTH_PATH.exists():
        return None
    data = json.loads(_CODEX_AUTH_PATH.read_text())
    tokens = data.get("tokens", {})
    return tokens.get("refresh_token")

"""Load/save OAuth tokens to gitignored tokens.json (project root)."""

from __future__ import annotations

import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TOKENS_PATH = _ROOT / "tokens.json"
TMP_PATH = _ROOT / "tokens.json.tmp"


def load_tokens() -> dict[str, str | int] | None:
    """Return token dict or None if file missing or invalid."""
    if not TOKENS_PATH.is_file():
        return None
    try:
        raw = TOKENS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    access = data.get("access_token")
    refresh = data.get("refresh_token")
    expires = data.get("expires_at")
    if not access or not refresh:
        return None
    try:
        exp = int(expires)
    except (TypeError, ValueError):
        return None
    return {
        "access_token": str(access),
        "refresh_token": str(refresh),
        "expires_at": exp,
    }


def save_tokens(access_token: str, refresh_token: str, expires_at: int) -> None:
    """Write tokens atomically; optional restrictive chmod on POSIX."""
    payload = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(expires_at),
    }
    text = json.dumps(payload, indent=2) + "\n"
    TMP_PATH.write_text(text, encoding="utf-8")
    os.replace(TMP_PATH, TOKENS_PATH)
    try:
        os.chmod(TOKENS_PATH, 0o600)
    except OSError:
        pass

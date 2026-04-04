#!/usr/bin/env python3
"""
One-time helper: open iSolarCloud OAuth in a browser, paste the authorization code,
and print ACCESS_TOKEN / REFRESH_TOKEN / TOKEN_EXPIRES_AT lines for config.py.

If your REDIRECT_URI points at a public site (e.g. a search-engine homepage), the browser
address bar may show no ?code= — the site can strip query parameters. In that case use
Developer Tools → Network (Preserve log) and copy the code from the first redirect URL.

Requires config.py with APP_KEY, SECRET_KEY, APP_ID, REDIRECT_URI, and ISOLAR_SERVER
(tokens in config can still be placeholders).
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import time
from urllib.parse import parse_qs, unquote, urlparse

from aiohttp import ClientSession
from pysolarcloud import Auth, Server

try:
    import config
except ImportError as e:
    print(
        "Missing config.py. Copy config.example.py to config.py and set APP_KEY, "
        "SECRET_KEY, APP_ID, REDIRECT_URI, and ISOLAR_SERVER (tokens can be dummy).",
        file=sys.stderr,
    )
    raise SystemExit(1) from e


def _server() -> Server:
    name = getattr(config, "ISOLAR_SERVER", "Europe")
    if isinstance(name, Server):
        return name
    try:
        return Server[name]
    except KeyError as e:
        valid = ", ".join(s.name for s in Server)
        raise SystemExit(f"Invalid ISOLAR_SERVER={name!r}. Use one of: {valid}") from e


def _require_filled(name: str, value: str | None) -> str:
    v = (value or "").strip()
    placeholders = (
        "",
        "YOUR_APP_KEY",
        "YOUR_SECRET_KEY",
        "YOUR_APPLICATION_ID",
        "YOUR_ACCESS_TOKEN",
        "YOUR_REFRESH_TOKEN",
    )
    if v in placeholders:
        raise SystemExit(
            f"Set {name} in config.py to your real developer-portal value (not the placeholder)."
        )
    return v


def _extract_authorization_code(raw: str) -> str:
    """Accept raw code or full redirect URL (query or fragment with code=)."""
    s = raw.strip().strip('"').strip("'")
    if not s:
        return ""
    if "code=" in s:
        parsed = urlparse(s if "://" in s else f"https://dummy.invalid/{s.lstrip('/')}")
        qs = parse_qs(parsed.query)
        if "code" in qs and qs["code"][0]:
            return qs["code"][0]
        if "#" in s:
            frag = s.split("#", 1)[1]
            qs = parse_qs(frag)
            if "code" in qs and qs["code"][0]:
                return qs["code"][0]
        m = re.search(r"code=([^&]+)", s)
        if m:
            return unquote(m.group(1))
    return s


def _print_instructions(auth_url: str) -> None:
    print()
    print("iSolarCloud OAuth — get tokens for config.py")
    print("=" * 50)
    print()
    print("1. In this project, config.py must already contain your real values for:")
    print("   ISOLAR_SERVER, APP_KEY, SECRET_KEY, APP_ID, REDIRECT_URI")
    print("   (REDIRECT_URI must match the redirect URL registered in the developer portal.)")
    print()
    print("2. Open this URL in a browser (log in to iSolarCloud if asked):")
    print()
    print(auth_url)
    print()
    print("3. After you approve access, the browser is sent to your REDIRECT_URI with")
    print("   ?code=... (and maybe other parameters) in the URL.")
    print()
    print("   First try: copy the full address from the address bar, or only the code value.")
    print()
    print("   If the address bar shows NO code (common when REDIRECT_URI is a big site like")
    print("   google.com / google.es): that page often loads a second redirect and drops the")
    print("   ?code= from what you see. The code was still in the first response.")
    print("   Then:")
    print("   - Open Developer Tools (F12) → Network tab.")
    print("   - Enable \"Preserve log\".")
    print("   - Run the OAuth flow again from step 2.")
    print("   - Find the first request to your redirect host (or the document that has")
    print("     \"code=\" in the URL).")
    print("   - Copy the full Request URL from that row (it should contain code=...).")
    print("   - Paste that entire URL below, or paste only the code parameter value.")
    print()
    print("   Better long-term: set REDIRECT_URI to http://127.0.0.1:PORT/path you control,")
    print("   register it exactly in the portal, so the code stays visible in the bar.")
    print()
    print("4. Paste below when prompted. The script will print lines to put in config.py.")
    print()


async def _exchange_code(auth: Auth, code: str, redirect_uri: str) -> dict:
    ts = await auth.async_fetch_tokens(code, redirect_uri)
    if isinstance(ts, dict) and "access_token" in ts:
        return ts
    print("Token response did not contain access_token:", ts, file=sys.stderr)
    raise SystemExit(2)


async def _run(*, url_only: bool) -> None:
    server = _server()
    app_key = _require_filled("APP_KEY", getattr(config, "APP_KEY", None))
    secret = _require_filled("SECRET_KEY", getattr(config, "SECRET_KEY", None))
    app_id = _require_filled("APP_ID", getattr(config, "APP_ID", None))
    redirect_uri = _require_filled("REDIRECT_URI", getattr(config, "REDIRECT_URI", None))
    if redirect_uri == "https://example.com/oauth/callback":
        raise SystemExit(
            "REDIRECT_URI in config.py is still the example URL. "
            "Set it to the redirect URL you registered in the developer portal."
        )

    async with ClientSession() as session:
        auth = Auth(server, app_key, secret, app_id, websession=session)
        auth_url = auth.auth_url(redirect_uri)

        if url_only:
            print(auth_url)
            return

        _print_instructions(auth_url)
        raw = input(
            "Paste redirect URL (or code). Use DevTools → Network if the bar has no code= : "
        ).strip()
        code = _extract_authorization_code(raw)
        if not code:
            print(
                "No authorization code found. If the address bar had no ?code=, open "
                "Developer Tools → Network, enable Preserve log, repeat the login, and copy "
                "the Request URL that contains code=.",
                file=sys.stderr,
            )
            raise SystemExit(2)

        ts = await _exchange_code(auth, code, redirect_uri)
        expires_in = int(ts.get("expires_in", 0) or 0)
        if expires_in <= 0:
            expires_in = 3600
        expires_at = int(time.time()) + expires_in - 20

        access = ts["access_token"]
        refresh = ts.get("refresh_token", "")
        print()
        print("Add or replace these lines in config.py (keep other settings as they are):")
        print()
        print(f'ACCESS_TOKEN = "{access}"')
        print(f'REFRESH_TOKEN = "{refresh}"')
        print(f"TOKEN_EXPIRES_AT = {expires_at}")
        print()
        print(f"# access token expires in ~{expires_in}s; TOKEN_EXPIRES_AT is Unix time with small margin.")
        print()


def main() -> None:
    p = argparse.ArgumentParser(description="Exchange iSolarCloud OAuth code for tokens (config.py).")
    p.add_argument(
        "--url-only",
        action="store_true",
        help="Only print the authorization URL (no code exchange).",
    )
    args = p.parse_args()
    asyncio.run(_run(url_only=args.url_only))


if __name__ == "__main__":
    main()

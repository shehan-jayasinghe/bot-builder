#!/usr/bin/env python3
"""Mint a short-lived JWT for an active Clerk session (Backend API).

The browser uses the Frontend API (/v1/client/sessions/.../tokens) with cookies.
For scripts/CI, use the Backend API with CLERK_SECRET_KEY instead.

Usage:
  poetry run python scripts/clerk_mint_token.py
  poetry run python scripts/clerk_mint_token.py --session-id sess_3G6R1apw8ifrkHaN8Mib3r1PItd
  poetry run python scripts/clerk_mint_token.py --export   # prints export BEARER_TOKEN=...
"""

from __future__ import annotations

import argparse
import sys

import httpx

from app.config import settings

DEFAULT_SESSION_ID = "sess_3G6R1apw8ifrkHaN8Mib3r1PItd"
CLERK_API = "https://api.clerk.com/v1"


def mint_session_token(*, session_id: str, expires_in_seconds: int = 3600) -> str:
    if not settings.clerk_secret_key:
        raise RuntimeError("CLERK_SECRET_KEY is not set in .env")

    url = f"{CLERK_API}/sessions/{session_id}/tokens"
    try:
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.clerk_secret_key}",
                "Content-Type": "application/json",
                "User-Agent": "bot-builder-seed/1.0",
            },
            json={"expires_in_seconds": expires_in_seconds},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise RuntimeError(
            f"Clerk token mint failed ({exc.response.status_code}): {detail}"
        ) from exc

    jwt = payload.get("jwt")
    if not jwt:
        raise RuntimeError(f"Clerk response missing jwt: {payload}")
    return str(jwt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint Clerk session JWT for API scripts")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--expires-in", type=int, default=3600)
    parser.add_argument(
        "--export",
        action="store_true",
        help="Print export BEARER_TOKEN='...' for shell",
    )
    args = parser.parse_args()

    token = mint_session_token(
        session_id=args.session_id,
        expires_in_seconds=args.expires_in,
    )
    if args.export:
        print(f"export BEARER_TOKEN='{token}'")
    else:
        print(token)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

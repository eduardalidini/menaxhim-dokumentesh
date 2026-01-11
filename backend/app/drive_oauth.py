from __future__ import annotations

import json
import secrets
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from .auth import require_role
from .config import get_google_oauth_client_json, get_public_base_url
from .db import consume_drive_oauth_state, create_drive_oauth_state, upsert_drive_oauth_token


_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _bad_request(message: str) -> Response:
    return JSONResponse({"error": {"code": "bad_request", "message": message}}, status_code=400)


def _redirect_uri() -> str:
    base = get_public_base_url()
    if not base:
        raise RuntimeError("PUBLIC_BASE_URL is not set (required for Google OAuth redirect URI)")
    return base.rstrip("/") + "/api/drive/auth/callback"


def _client_config() -> dict:
    raw = get_google_oauth_client_json()
    if not raw:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_JSON is not set")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid GOOGLE_OAUTH_CLIENT_JSON: {e}") from e


def drive_auth_start(request: Request) -> Response:
    # Admin-only: this connects the backend to the user's Drive.
    require_role(request, {"admin"})

    from google_auth_oauthlib.flow import Flow

    state = secrets.token_urlsafe(24)
    create_drive_oauth_state(state)

    flow = Flow.from_client_config(_client_config(), scopes=_DRIVE_SCOPES, state=state)
    flow.redirect_uri = _redirect_uri()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return RedirectResponse(auth_url, status_code=302)


def drive_auth_url(request: Request) -> Response:
    require_role(request, {"admin"})

    from google_auth_oauthlib.flow import Flow

    state = secrets.token_urlsafe(24)
    create_drive_oauth_state(state)

    flow = Flow.from_client_config(_client_config(), scopes=_DRIVE_SCOPES, state=state)
    flow.redirect_uri = _redirect_uri()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return JSONResponse({"auth_url": auth_url})


def drive_auth_callback(request: Request) -> Response:
    # Admin-only: finishes the OAuth code exchange.
    require_role(request, {"admin"})

    code = (request.query_params.get("code") or "").strip()
    state = (request.query_params.get("state") or "").strip()
    error = (request.query_params.get("error") or "").strip()

    if error:
        return _bad_request(f"Google OAuth error: {error}")

    if not code or not state:
        return _bad_request("Missing code/state")

    if not consume_drive_oauth_state(state):
        return _bad_request("Invalid or expired state")

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(_client_config(), scopes=_DRIVE_SCOPES, state=state)
    flow.redirect_uri = _redirect_uri()

    flow.fetch_token(code=code)

    creds = flow.credentials
    refresh_token = getattr(creds, "refresh_token", None)
    if not refresh_token:
        return _bad_request(
            "Google OAuth did not return a refresh_token. "
            "Try again (we request prompt=consent), and ensure you are not using an account that blocks offline access."
        )

    client_cfg = flow.client_config
    installed = client_cfg.get("installed") or client_cfg.get("web") or {}

    token_uri = installed.get("token_uri") or "https://oauth2.googleapis.com/token"
    client_id = installed.get("client_id")
    client_secret = installed.get("client_secret")

    if not client_id or not client_secret:
        return _bad_request("OAuth client config missing client_id/client_secret")

    upsert_drive_oauth_token(
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
    )

    # After success, redirect to docs with a small hint.
    qs = urlencode({"drive": "connected"})
    return RedirectResponse(f"/docs?{qs}", status_code=302)

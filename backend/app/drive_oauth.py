from __future__ import annotations

import json
import secrets
from urllib.parse import urlencode

from datetime import datetime, timezone

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from .auth import get_bearer_token, require_role
from .config import get_frontend_base_url, get_google_oauth_client_json, get_public_base_url
from .db import (
    consume_drive_oauth_state,
    create_drive_oauth_state,
    create_drive_oauth_state_with_token,
    get_drive_oauth_state_with_token,
    delete_drive_oauth_token_for_user,
    get_drive_oauth_token_meta_for_user,
    upsert_drive_oauth_token_for_user,
)


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
    require_role(request, {"staf", "sekretaria", "admin"})

    from google_auth_oauthlib.flow import Flow

    state = secrets.token_urlsafe(24)
    create_drive_oauth_state(state)

    # Store user token in database with the state for callback validation
    user_token = get_bearer_token(request)
    if not user_token:
        return _bad_request("Missing authentication token")
    
    # Store the admin token with the state for callback retrieval
    from .db import create_drive_oauth_state_with_token
    create_drive_oauth_state_with_token(state, user_token)

    flow = Flow.from_client_config(_client_config(), scopes=_DRIVE_SCOPES, state=state)
    flow.redirect_uri = _redirect_uri()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return RedirectResponse(auth_url, status_code=302)


def drive_auth_url(request: Request) -> Response:
    require_role(request, {"staf", "sekretaria", "admin"})

    from google_auth_oauthlib.flow import Flow

    state = secrets.token_urlsafe(24)
    create_drive_oauth_state(state)

    user_token = get_bearer_token(request)
    if not user_token:
        return _bad_request("Missing authentication token")
    create_drive_oauth_state_with_token(state, user_token)

    flow = Flow.from_client_config(_client_config(), scopes=_DRIVE_SCOPES, state=state)
    flow.redirect_uri = _redirect_uri()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return JSONResponse({"auth_url": auth_url})


def drive_auth_callback(request: Request) -> Response:
    # Authenticated user: finishes the OAuth code exchange.
    # For OAuth callback, retrieve token from database using state
    code = (request.query_params.get("code") or "").strip()
    state = (request.query_params.get("state") or "").strip()
    error = (request.query_params.get("error") or "").strip()

    if error:
        return _bad_request(f"Google OAuth error: {error}")

    if not code or not state:
        return _bad_request("Missing code/state")

    # Retrieve and validate the stored user token
    stored_data = get_drive_oauth_state_with_token(state)
    if not stored_data:
        return _bad_request("Invalid or expired state")
    
    user_token = stored_data.get("token")
    if not user_token:
        return _bad_request("Missing authentication token")
    
    try:
        from .auth import decode_token
        payload = decode_token(user_token)
        user = {
            "id": int(payload.get("sub")),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
        if user.get("role") not in {"staf", "sekretaria", "admin"}:
            return _bad_request("Access required")
    except Exception:
        return _bad_request("Invalid authentication token")

    # Consume the state (original function)
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

    # Extract OAuth client metadata from the configured client JSON.
    # google-auth-oauthlib's internal client_config shape can vary between versions,
    # so rely on our parsed env config.
    client_cfg = _client_config()
    oauth_section = client_cfg.get("web") or client_cfg.get("installed") or client_cfg

    token_uri = oauth_section.get("token_uri") or "https://oauth2.googleapis.com/token"
    client_id = oauth_section.get("client_id")
    client_secret = oauth_section.get("client_secret")

    if not client_id or not client_secret:
        return _bad_request("OAuth client config missing client_id/client_secret")

    upsert_drive_oauth_token_for_user(
        user_id=int(user["id"]),
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
    )

    # After success, redirect to frontend if configured, otherwise to docs.
    qs = urlencode({"drive": "connected", "at": datetime.now(timezone.utc).isoformat()})
    frontend = (get_frontend_base_url() or "").strip()
    if frontend:
        return RedirectResponse(f"{frontend.rstrip('/')}/drive?{qs}", status_code=302)
    return RedirectResponse(f"/docs?{qs}", status_code=302)


def drive_status(request: Request) -> Response:
    user = require_role(request, {"staf", "sekretaria", "admin"})
    token = get_drive_oauth_token_meta_for_user(int(user["id"]))
    if not token:
        return JSONResponse({"connected": False, "connected_at": None, "updated_at": None})
    created_at = token.get("created_at")
    updated_at = token.get("updated_at")
    return JSONResponse(
        {
            "connected": True,
            "connected_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
            "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else updated_at,
        }
    )


def drive_disconnect(request: Request) -> Response:
    user = require_role(request, {"staf", "sekretaria", "admin"})
    ok = delete_drive_oauth_token_for_user(int(user["id"]))
    return JSONResponse({"connected": False, "disconnected": bool(ok)})

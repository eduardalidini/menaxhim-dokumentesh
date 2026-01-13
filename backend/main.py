from __future__ import annotations

import json
import os

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.schemas import SchemaGenerator
from starlette.routing import Route
from starlette.exceptions import HTTPException

from backend.app.auth import create_access_token, decode_token, get_bearer_token, hash_password, verify_password
from backend.app.config import get_seed_admin_email, get_seed_admin_password
from backend.app.db import (
    add_allowed_email,
    create_user,
    get_user_by_email,
    init_db,
    is_email_allowed,
    list_allowed_emails,
    remove_allowed_email,
    update_user_credentials_by_email,
    scalar,
)
from backend.app.drive_oauth import drive_auth_callback, drive_auth_start, drive_auth_url, drive_disconnect, drive_status

from backend.app.documents import (
    create_document,
    delete_document,
    get_document,
    generate_ai_summary,
    list_documents,
    update_document,
    archive_document,
    unarchive_document,
    replace_document_file,
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None

        token = get_bearer_token(request)
        if token:
            try:
                payload = decode_token(token)
                request.state.user = {
                    "id": int(payload.get("sub")),
                    "email": payload.get("email"),
                    "role": payload.get("role"),
                }
            except Exception:
                # Invalid token -> treat as unauthenticated
                request.state.user = None

        return await call_next(request)


def health(request) -> Response:
    return JSONResponse({"status": "ok"})


def health_db(request) -> Response:
    value = scalar("SELECT 1")
    return JSONResponse({"status": "ok", "db": value})


async def login(request: Request) -> Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": {"code": "bad_request", "message": "Invalid JSON"}}, status_code=400)

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return JSONResponse(
            {"error": {"code": "bad_request", "message": "email and password are required"}},
            status_code=400,
        )

    user = get_user_by_email(email)
    if not user:
        return JSONResponse({"error": {"code": "invalid_credentials", "message": "Invalid credentials"}}, status_code=401)

    # For department-only usage: non-admin users must be whitelisted by admin.
    if user.get("role") != "admin" and not is_email_allowed(email):
        return JSONResponse(
            {"error": {"code": "forbidden", "message": "Email is not allowed"}},
            status_code=403,
        )

    if not verify_password(password, user["password_hash"]):
        return JSONResponse({"error": {"code": "invalid_credentials", "message": "Invalid credentials"}}, status_code=401)

    token = create_access_token(user_id=int(user["id"]), email=user["email"], role=user["role"])
    return JSONResponse({"access_token": token, "token_type": "bearer", "role": user["role"]})


def _bad_request(message: str) -> Response:
    return JSONResponse({"error": {"code": "bad_request", "message": message}}, status_code=400)


async def admin_list_allowed_emails(request: Request) -> Response:
    from backend.app.auth import require_role

    require_role(request, {"admin"})
    return JSONResponse({"items": list_allowed_emails()})


async def admin_add_allowed_email(request: Request) -> Response:
    from backend.app.auth import require_role

    require_role(request, {"admin"})
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return _bad_request("Invalid JSON")

    email = (body.get("email") or "").strip().lower()
    if not email:
        return _bad_request("email is required")

    created = add_allowed_email(email)
    return JSONResponse(created, status_code=201)


async def admin_remove_allowed_email(request: Request) -> Response:
    from backend.app.auth import require_role

    require_role(request, {"admin"})
    email = (request.path_params.get("email") or "").strip().lower()
    if not email:
        return _bad_request("email is required")

    ok = remove_allowed_email(email)
    if not ok:
        return JSONResponse({"error": {"code": "not_found", "message": "Email not found"}}, status_code=404)
    return JSONResponse({"status": "deleted"})


async def admin_create_staff_user(request: Request) -> Response:
    from backend.app.auth import require_role

    require_role(request, {"admin"})
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return _bad_request("Invalid JSON")

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    role = (body.get("role") or "staf").strip()

    if not email or not password:
        return _bad_request("email and password are required")
    if role not in {"staf", "sekretaria"}:
        return _bad_request("role must be staf or sekretaria")

    # Ensure user is allowed by admin whitelist.
    add_allowed_email(email)

    existing = get_user_by_email(email)
    if existing:
        if existing.get("role") == "admin":
            return JSONResponse({"error": {"code": "forbidden", "message": "Cannot modify admin user"}}, status_code=403)

        updated = update_user_credentials_by_email(email=email, password_hash=hash_password(password), role=role)
        if not updated:
            return JSONResponse({"error": {"code": "internal_error", "message": "Failed to update user"}}, status_code=500)
        return JSONResponse({"status": "updated", "user": updated}, status_code=200)

    created = create_user(email, hash_password(password), role=role)
    return JSONResponse({"status": "created", "user": created}, status_code=201)


def me(request: Request) -> Response:
    if not request.state.user:
        return JSONResponse({"error": {"code": "unauthorized", "message": "Missing or invalid token"}}, status_code=401)
    return JSONResponse({"user": request.state.user})


schema_generator = SchemaGenerator(
    {"openapi": "3.0.0", "info": {"title": "Menaxhim Dokumentash API", "version": "1.0.0"}}
)


def openapi(request: Request) -> Response:
    schema = schema_generator.get_schema(routes=app.routes)
    return JSONResponse(schema)


def docs(request: Request) -> Response:
    html = """<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Menaxhim Dokumentash API Docs</title>
    <link rel=\"stylesheet\" href=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui.css\" />
  </head>
  <body>
    <div id=\"swagger-ui\"></div>
    <script src=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js\"></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
      });
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


routes = [
    Route("/health", endpoint=health, methods=["GET"]),
    Route("/health/db", endpoint=health_db, methods=["GET"]),
    Route("/openapi.json", endpoint=openapi, methods=["GET"]),
    Route("/docs", endpoint=docs, methods=["GET"]),
    Route("/api/auth/login", endpoint=login, methods=["POST"]),
    Route("/api/auth/me", endpoint=me, methods=["GET"]),
    Route("/api/admin/allowed-emails", endpoint=admin_list_allowed_emails, methods=["GET"]),
    Route("/api/admin/allowed-emails", endpoint=admin_add_allowed_email, methods=["POST"]),
    Route("/api/admin/allowed-emails/{email:str}", endpoint=admin_remove_allowed_email, methods=["DELETE"]),
    Route("/api/admin/users", endpoint=admin_create_staff_user, methods=["POST"]),
    Route("/api/drive/auth/start", endpoint=drive_auth_start, methods=["GET"]),
    Route("/api/drive/auth/url", endpoint=drive_auth_url, methods=["GET"]),
    Route("/api/drive/auth/callback", endpoint=drive_auth_callback, methods=["GET"]),
    Route("/api/drive/status", endpoint=drive_status, methods=["GET"]),
    Route("/api/drive/disconnect", endpoint=drive_disconnect, methods=["POST"]),
    Route("/api/documents", endpoint=list_documents, methods=["GET"]),
    Route("/api/documents", endpoint=create_document, methods=["POST"]),
    Route("/api/documents/{doc_id:int}", endpoint=get_document, methods=["GET"]),
    Route("/api/documents/{doc_id:int}/ai-summary", endpoint=generate_ai_summary, methods=["POST"]),
    Route("/api/documents/{doc_id:int}", endpoint=update_document, methods=["PUT"]),
    Route("/api/documents/{doc_id:int}/file", endpoint=replace_document_file, methods=["PUT"]),
    Route("/api/documents/{doc_id:int}/archive", endpoint=archive_document, methods=["PATCH"]),
    Route("/api/documents/{doc_id:int}/unarchive", endpoint=unarchive_document, methods=["PATCH"]),
    Route("/api/documents/{doc_id:int}", endpoint=delete_document, methods=["DELETE"]),
]


debug = (os.getenv("DEBUG") or "").strip().lower() in {"1", "true", "yes"}
app = Starlette(debug=debug, routes=routes)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    message = str(exc)
    if message == "unauthorized":
        return JSONResponse({"error": {"code": "unauthorized", "message": "Missing or invalid token"}}, status_code=401)
    if message == "forbidden":
        message = "Forbidden"
    return JSONResponse({"error": {"code": "forbidden", "message": message}}, status_code=403)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize Starlette's default errors into our JSON format.
    code = "http_error"
    if exc.status_code == 404:
        code = "not_found"
    elif exc.status_code == 405:
        code = "method_not_allowed"
    return JSONResponse(
        {"error": {"code": code, "message": exc.detail}},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Always return JSON so Postman/browser doesn't "spin" without feedback.
    try:
        import psycopg

        # PostgreSQL unique violation -> 409 conflict
        if isinstance(exc, psycopg.Error) and getattr(exc, "sqlstate", None) == "23505":
            return JSONResponse(
                {"error": {"code": "conflict", "message": "Resource already exists"}},
                status_code=409,
            )
    except Exception:
        pass

    return JSONResponse(
        {"error": {"code": "internal_error", "message": str(exc)}},
        status_code=500,
    )


@app.on_event("startup")
async def on_startup() -> None:
    # init_db is sync; run it at startup.
    init_db()

    # Optional seed admin for first login (set in .env).
    seed_email = get_seed_admin_email()
    seed_password = get_seed_admin_password()
    if seed_email and seed_password:
        seed_email = seed_email.strip().lower()
        if not get_user_by_email(seed_email):
            from backend.app.auth import hash_password

            create_user(seed_email, hash_password(seed_password), role="admin")

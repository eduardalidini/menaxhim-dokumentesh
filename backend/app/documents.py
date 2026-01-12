from __future__ import annotations

import json
from datetime import datetime

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .auth import require_auth, require_role
from .config import get_drive_folder_id
from .db import (
    archive_document_by_id,
    create_document_row,
    delete_document_by_id,
    get_document_by_id,
    get_document_uploader_id,
    list_documents_rows,
    update_document_file_by_id,
    update_document_by_id,
)
from .drive import delete_file_from_drive, download_file_from_drive, update_file_content_in_drive, upload_file_to_drive


def _forbidden(message: str = "forbidden") -> Response:
    return JSONResponse({"error": {"code": "forbidden", "message": message}}, status_code=403)


def _require_owner_or_admin(request: Request, *, doc_id: int) -> dict | None:
    user = require_role(request, {"staf", "sekretaria", "admin"})
    if user.get("role") == "admin":
        return user

    uploader_id = get_document_uploader_id(doc_id)
    if uploader_id is None:
        return None
    if int(uploader_id) != int(user["id"]):
        raise PermissionError("forbidden")
    return user


def _bad_request(message: str) -> Response:
    return JSONResponse({"error": {"code": "bad_request", "message": message}}, status_code=400)


def _not_found() -> Response:
    return JSONResponse({"error": {"code": "not_found", "message": "Document not found"}}, status_code=404)


def list_documents(request: Request) -> Response:
    require_auth(request)

    query = (request.query_params.get("query") or "").strip()
    category = (request.query_params.get("category") or "").strip()
    status = (request.query_params.get("status") or "").strip() or "active"
    date_from = (request.query_params.get("from") or "").strip()
    date_to = (request.query_params.get("to") or "").strip()

    page = int(request.query_params.get("page") or 1)
    page_size = int(request.query_params.get("page_size") or 20)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    def parse_date(value: str) -> datetime | None:
        if not value:
            return None
        try:
            # Accept ISO date or datetime
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    from_dt = parse_date(date_from)
    to_dt = parse_date(date_to)
    if date_from and not from_dt:
        return _bad_request("Invalid 'from' date. Use ISO format (e.g. 2026-01-11 or 2026-01-11T10:00:00)")
    if date_to and not to_dt:
        return _bad_request("Invalid 'to' date. Use ISO format (e.g. 2026-01-11 or 2026-01-11T10:00:00)")

    rows = list_documents_rows(
        query=query or None,
        category=category or None,
        status=status or None,
        from_dt=from_dt,
        to_dt=to_dt,
        page=page,
        page_size=page_size,
    )
    return JSONResponse({"items": rows, "page": page, "page_size": page_size})


def get_document(request: Request) -> Response:
    doc_id = int(request.path_params["doc_id"])
    doc = get_document_by_id(doc_id)
    if not doc:
        return _not_found()
    return JSONResponse(doc)


def generate_ai_summary(request: Request) -> Response:
    user = require_role(request, {"staf", "sekretaria", "admin"})

    doc_id = int(request.path_params["doc_id"])
    doc = get_document_by_id(doc_id)
    if not doc:
        return _not_found()

    from .config import get_gemini_api_key

    api_key = get_gemini_api_key()
    if not api_key:
        return _bad_request("GEMINI_API_KEY is not configured")

    uploader_id = get_document_uploader_id(doc_id)
    drive_file_id = str(doc["drive_file_id"])

    file_bytes = None
    for candidate_user_id in (
        int(user["id"]),
        int(uploader_id) if uploader_id is not None else None,
        -1,
    ):
        if candidate_user_id is None:
            continue
        try:
            file_bytes = download_file_from_drive(user_id=int(candidate_user_id), drive_file_id=drive_file_id)
            break
        except Exception:
            continue

    if file_bytes is None:
        return _bad_request("Unable to download file for AI summary")

    from .gemini import generate_summary

    try:
        summary = generate_summary(
            api_key=api_key,
            title=str(doc.get("title") or ""),
            category=str(doc.get("category") or ""),
            description=doc.get("description"),
            tags=doc.get("tags"),
            mime_type=str(doc.get("file_type") or "application/octet-stream"),
            file_bytes=file_bytes,
        )
    except Exception as e:
        return _bad_request(f"AI summary generation failed: {e}")

    return JSONResponse({"doc_id": doc_id, "ai_summary": summary})


async def create_document(request: Request) -> Response:
    user = require_role(request, {"staf", "sekretaria", "admin"})

    content_type = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" not in content_type:
        return _bad_request("Content-Type must be multipart/form-data")

    form = await request.form()
    title = (form.get("title") or "").strip()
    category = (form.get("category") or "").strip()
    description = (form.get("description") or "").strip() or None
    tags = (form.get("tags") or "").strip() or None
    upload = form.get("file")

    if not title:
        return _bad_request("title is required")
    if not category:
        return _bad_request("category is required")
    if not upload:
        return _bad_request("file is required")
    if not isinstance(upload, UploadFile):
        return _bad_request("file must be a file upload")

    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    file_content_type = (upload.content_type or "").strip().lower()
    if file_content_type not in allowed_types:
        return _bad_request("Invalid file type. Allowed: pdf, docx")

    content = await upload.read()
    max_bytes = 10 * 1024 * 1024
    if len(content) > max_bytes:
        return _bad_request("File too large. Max size is 10MB")

    try:
        drive = upload_file_to_drive(
            user_id=int(user["id"]),
            filename=upload.filename or "document",
            content_type=file_content_type,
            content=content,
            folder_id=get_drive_folder_id(),
        )
    except RuntimeError as e:
        return _bad_request(str(e))
    drive_file_id = (drive.get("drive_file_id") or "").strip()
    web_view_link = (drive.get("web_view_link") or "").strip()
    if not drive_file_id or not web_view_link:
        raise RuntimeError("Drive upload did not return required fields")

    doc = create_document_row(
        title=title,
        category=category,
        description=description,
        tags=tags,
        file_type=file_content_type,
        drive_file_id=drive_file_id,
        web_view_link=web_view_link,
        uploaded_by_user_id=int(user["id"]),
    )
    return JSONResponse(doc, status_code=201)


async def update_document(request: Request) -> Response:
    require_role(request, {"sekretaria", "admin"})

    doc_id = int(request.path_params["doc_id"])

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return _bad_request("Invalid JSON")

    title = body.get("title")
    category = body.get("category")
    description = body.get("description")
    tags = body.get("tags")

    if title is not None:
        title = str(title).strip()
        if not title:
            return _bad_request("title cannot be empty")

    if category is not None:
        category = str(category).strip()
        if not category:
            return _bad_request("category cannot be empty")

    if description is not None:
        description = str(description).strip() or None

    if tags is not None:
        tags = str(tags).strip() or None

    updated = update_document_by_id(
        doc_id=doc_id,
        title=title,
        category=category,
        description=description,
        tags=tags,
    )

    if not updated:
        return _not_found()

    return JSONResponse(updated)


def archive_document(request: Request) -> Response:
    doc_id = int(request.path_params["doc_id"])

    try:
        _require_owner_or_admin(request, doc_id=doc_id)
    except PermissionError:
        return _forbidden("Only the uploader (or admin) can archive this document")

    updated = archive_document_by_id(doc_id)
    if not updated:
        return _not_found()
    return JSONResponse(updated)


def delete_document(request: Request) -> Response:
    doc_id = int(request.path_params["doc_id"])

    try:
        user = _require_owner_or_admin(request, doc_id=doc_id)
    except PermissionError:
        return _forbidden("Only the uploader (or admin) can delete this document")
    if not user:
        return _not_found()

    doc = get_document_by_id(doc_id)
    if not doc:
        return _not_found()

    uploader_id = get_document_uploader_id(doc_id)
    drive_file_id = str(doc["drive_file_id"])
    last_err: Exception | None = None
    for candidate_user_id in (
        int(user["id"]),
        int(uploader_id) if uploader_id is not None else None,
        -1,
    ):
        if candidate_user_id is None:
            continue
        try:
            delete_file_from_drive(user_id=int(candidate_user_id), drive_file_id=drive_file_id)
            last_err = None
            break
        except Exception as e:
            last_err = e
            continue
    if last_err is not None:
        return _bad_request(f"Failed to delete file from Drive: {last_err}")

    ok = delete_document_by_id(doc_id)
    if not ok:
        return _not_found()
    return JSONResponse({"status": "deleted"})


async def replace_document_file(request: Request) -> Response:
    doc_id = int(request.path_params["doc_id"])

    try:
        user = _require_owner_or_admin(request, doc_id=doc_id)
    except PermissionError:
        return _forbidden("Only the uploader (or admin) can replace the file for this document")
    if not user:
        return _not_found()

    doc = get_document_by_id(doc_id)
    if not doc:
        return _not_found()

    content_type = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" not in content_type:
        return _bad_request("Content-Type must be multipart/form-data")

    form = await request.form()
    upload = form.get("file")
    if not upload:
        return _bad_request("file is required")
    if not isinstance(upload, UploadFile):
        return _bad_request("file must be a file upload")

    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    file_content_type = (upload.content_type or "").strip().lower()
    if file_content_type not in allowed_types:
        return _bad_request("Invalid file type. Allowed: pdf, docx")

    content = await upload.read()
    max_bytes = 10 * 1024 * 1024
    if len(content) > max_bytes:
        return _bad_request("File too large. Max size is 10MB")

    try:
        uploader_id = get_document_uploader_id(doc_id)
        drive_file_id = str(doc["drive_file_id"])
        last_err: Exception | None = None
        drive = None
        for candidate_user_id in (
            int(user["id"]),
            int(uploader_id) if uploader_id is not None else None,
            -1,
        ):
            if candidate_user_id is None:
                continue
            try:
                drive = update_file_content_in_drive(
                    user_id=int(candidate_user_id),
                    drive_file_id=drive_file_id,
                    content_type=file_content_type,
                    content=content,
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                continue
        if last_err is not None or drive is None:
            raise RuntimeError(str(last_err) if last_err is not None else "Drive update failed")
    except RuntimeError as e:
        return _bad_request(str(e))
    web_view_link = (drive.get("web_view_link") or "").strip() or str(doc["web_view_link"])

    updated = update_document_file_by_id(
        doc_id=doc_id,
        file_type=file_content_type,
        web_view_link=web_view_link,
    )
    if not updated:
        return _not_found()
    return JSONResponse(updated)

from __future__ import annotations

import json
import os
import tempfile
from io import BytesIO

from dotenv import load_dotenv

from .db import get_drive_oauth_token_for_user


load_dotenv()


_temp_credentials_path: str | None = None


def _ensure_credentials_file() -> str:
    global _temp_credentials_path

    json_value = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_value:
        try:
            # Validate early so errors are clear (common issue: malformed env JSON).
            json.loads(json_value)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                "Invalid GOOGLE_CREDENTIALS_JSON. "
                "It must be the full service account JSON as a single valid JSON string. "
                f"JSON error at line {e.lineno} col {e.colno}: {e.msg}"
            ) from e

        if _temp_credentials_path:
            return _temp_credentials_path

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        try:
            tmp.write(json_value)
            tmp.flush()
        finally:
            tmp.close()

        _temp_credentials_path = tmp.name
        return _temp_credentials_path

    raise RuntimeError("Missing Google credentials. Set GOOGLE_CREDENTIALS_JSON.")


def get_drive_service(*, user_id: int):
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google.oauth2 import service_account

        # 1) Prefer OAuth (user account) so uploads work on personal Google Drive
        token = get_drive_oauth_token_for_user(user_id)
        if token:
            creds = Credentials(
                token=None,
                refresh_token=str(token["refresh_token"]),
                token_uri=str(token["token_uri"]),
                client_id=str(token["client_id"]),
                client_secret=str(token["client_secret"]),
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            # Ensure access token is available.
            creds.refresh(Request())
            return build("drive", "v3", credentials=creds, cache_discovery=False)

        # 2) Fallback: service account (requires Workspace Shared Drives to avoid quota limits)
        json_value = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if json_value:
            credentials_path = _ensure_credentials_file()
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            return build("drive", "v3", credentials=credentials, cache_discovery=False)

        raise RuntimeError("Google Drive is not connected for this user. Connect it via /api/drive/auth/url")
    except Exception as e:
        raise RuntimeError(
            "Failed to initialize Google Drive client. "
            "If using OAuth, ensure GOOGLE_OAUTH_CLIENT_JSON and PUBLIC_BASE_URL are set, then visit /api/drive/auth/start (admin-only). "
            "If using Service Account, check GOOGLE_CREDENTIALS_JSON (must be valid JSON) and that it contains "
            "service account fields like client_email and token_uri. "
            f"Inner error: {e}"
        ) from e


def _extract_drive_http_error(e: Exception) -> tuple[int | None, str | None, str | None]:
    status = getattr(getattr(e, "resp", None), "status", None)
    raw: str | None = None
    try:
        raw = getattr(e, "content", None)
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        if not raw:
            return status, None, None

        payload = json.loads(raw)
        err = payload.get("error") if isinstance(payload, dict) else None
        message = err.get("message") if isinstance(err, dict) else None

        reason = None
        details = err.get("errors") if isinstance(err, dict) else None
        if isinstance(details, list) and details:
            d0 = details[0]
            if isinstance(d0, dict):
                reason = d0.get("reason")

        return status, reason, message
    except Exception:
        return status, None, raw


def _ensure_folder_writable(*, service, folder_id: str) -> None:
    from googleapiclient.errors import HttpError

    try:
        folder = (
            service.files()
            .get(
                fileId=folder_id,
                fields="id, name, mimeType, driveId, capabilities(canAddChildren)",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        status, reason, message = _extract_drive_http_error(e)
        if status in {403, 404}:
            raise RuntimeError(
                "Google Drive folder access check failed. "
                "Make sure the connected Google account has access to the DRIVE_FOLDER_ID folder (and the Shared Drive if applicable). "
                f"Drive reason: {reason or 'unknown'}. Message: {message or 'unknown'}"
            ) from e
        raise

    caps = folder.get("capabilities") if isinstance(folder, dict) else None
    can_add = None
    if isinstance(caps, dict):
        can_add = caps.get("canAddChildren")

    if can_add is False:
        raise RuntimeError(
            "Google Drive upload failed: the connected Google account is not allowed to upload into the configured folder. "
            "The account needs at least Contributor/Editor (Shared Drive) or Editor (My Drive folder) permissions on that folder."
        )


def upload_file_to_drive(*, user_id: int, filename: str, content_type: str, content: bytes, folder_id: str) -> dict:
    from googleapiclient.http import MediaIoBaseUpload
    from googleapiclient.errors import HttpError

    service = get_drive_service(user_id=user_id)
    _ensure_folder_writable(service=service, folder_id=folder_id)

    file_metadata: dict[str, object] = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(BytesIO(content), mimetype=content_type, resumable=False)
    try:
        created = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        status, reason, message = _extract_drive_http_error(e)
        if status in {403, 404}:
            raise RuntimeError(
                "Google Drive upload failed: the connected Google account does not have access to the configured folder. "
                "Make sure the account has permission to the DRIVE_FOLDER_ID folder (share the folder with that email), "
                "or change DRIVE_FOLDER_ID to a folder the account owns. "
                f"Drive reason: {reason or 'unknown'}. Message: {message or 'unknown'}"
            ) from e
        message = str(e)
        if "storageQuotaExceeded" in message or "do not have storage quota" in message:
            raise RuntimeError(
                "Google Drive upload failed: Service Accounts do not have storage quota. "
                "Use a Shared Drive (Google Workspace) and add the service account as a member, "
                "then set DRIVE_FOLDER_ID to a folder inside that Shared Drive."
            ) from e
        raise
    return {
        "drive_file_id": created.get("id"),
        "web_view_link": created.get("webViewLink"),
    }


def update_file_content_in_drive(*, user_id: int, drive_file_id: str, content_type: str, content: bytes) -> dict:
    from googleapiclient.http import MediaIoBaseUpload
    from googleapiclient.errors import HttpError

    service = get_drive_service(user_id=user_id)

    media = MediaIoBaseUpload(BytesIO(content), mimetype=content_type, resumable=False)
    try:
        updated = (
            service.files()
            .update(
                fileId=drive_file_id,
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        status = getattr(getattr(e, "resp", None), "status", None)
        if status in {403, 404}:
            raise RuntimeError(
                "Google Drive update failed: the connected Google account does not have permission to modify this file. "
                "Ensure the account that connected Drive is allowed to access/edit the file and folder."
            ) from e
        message = str(e)
        if "storageQuotaExceeded" in message or "do not have storage quota" in message:
            raise RuntimeError(
                "Google Drive update failed: Service Accounts do not have storage quota. "
                "Use a Shared Drive (Google Workspace) and add the service account as a member."
            ) from e
        raise
    return {
        "drive_file_id": updated.get("id"),
        "web_view_link": updated.get("webViewLink"),
    }


def delete_file_from_drive(*, user_id: int, drive_file_id: str) -> None:
    service = get_drive_service(user_id=user_id)
    service.files().delete(fileId=drive_file_id, supportsAllDrives=True).execute()


def download_file_from_drive(*, user_id: int, drive_file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload

    service = get_drive_service(user_id=user_id)

    request = service.files().get_media(fileId=drive_file_id, supportsAllDrives=True)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()

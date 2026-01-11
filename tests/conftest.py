import sys
from pathlib import Path
import os

import pytest
from starlette.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(monkeypatch):
    os.environ.setdefault("JWT_SECRET", "test_secret")
    os.environ.setdefault("JWT_EXPIRES_MINUTES", "60")

    import backend.main as main

    # Avoid DB access during startup
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "get_seed_admin_email", lambda: None)
    monkeypatch.setattr(main, "get_seed_admin_password", lambda: None)
    monkeypatch.setattr(main, "scalar", lambda sql: 1)

    # Create a test user for login
    test_user = {
        "id": 1,
        "email": "admin@example.com",
        "password_hash": None,
        "role": "admin",
    }

    from backend.app.auth import hash_password

    test_user["password_hash"] = hash_password("Admin123!")

    monkeypatch.setattr(main, "get_user_by_email", lambda email: test_user if email == test_user["email"] else None)

    # Documents DB calls
    import backend.app.documents as documents

    monkeypatch.setattr(documents, "list_documents_rows", lambda **kwargs: [])
    monkeypatch.setattr(
        documents,
        "get_document_by_id",
        lambda doc_id: {
            "id": doc_id,
            "title": "Doc",
            "description": None,
            "category": "request",
            "tags": None,
            "file_type": "application/pdf",
            "drive_file_id": "drive123",
            "web_view_link": "https://drive.google.com/file/d/drive123/view",
            "status": "active",
            "ai_summary": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        },
    )

    monkeypatch.setattr(
        documents,
        "create_document_row",
        lambda **kwargs: {
            "id": 1,
            "title": kwargs["title"],
            "description": kwargs.get("description"),
            "category": kwargs["category"],
            "tags": kwargs.get("tags"),
            "file_type": kwargs["file_type"],
            "drive_file_id": kwargs["drive_file_id"],
            "web_view_link": kwargs["web_view_link"],
            "status": "active",
            "ai_summary": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        },
    )

    monkeypatch.setattr(
        documents,
        "archive_document_by_id",
        lambda doc_id: {
            "id": doc_id,
            "title": "Doc",
            "description": None,
            "category": "request",
            "tags": None,
            "file_type": "application/pdf",
            "drive_file_id": "drive123",
            "web_view_link": "https://drive.google.com/file/d/drive123/view",
            "status": "archived",
            "ai_summary": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-02T00:00:00",
        },
    )
    monkeypatch.setattr(documents, "delete_document_by_id", lambda doc_id: True)
    monkeypatch.setattr(
        documents,
        "update_document_file_by_id",
        lambda **kwargs: {
            "id": kwargs["doc_id"],
            "title": "Doc",
            "description": None,
            "category": "request",
            "tags": None,
            "file_type": kwargs["file_type"],
            "drive_file_id": "drive123",
            "web_view_link": kwargs["web_view_link"],
            "status": "active",
            "ai_summary": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-02T00:00:00",
        },
    )

    # Drive operations mocked
    import backend.app.drive as drive

    monkeypatch.setattr(drive, "delete_file_from_drive", lambda **kwargs: None)
    monkeypatch.setattr(
        drive,
        "update_file_content_in_drive",
        lambda **kwargs: {"drive_file_id": kwargs["drive_file_id"], "web_view_link": "https://drive/new"},
    )

    monkeypatch.setattr(
        drive,
        "upload_file_to_drive",
        lambda **kwargs: {"drive_file_id": "drive123", "web_view_link": "https://drive/new"},
    )

    # documents.py imports these functions directly, so we must patch there too.
    monkeypatch.setattr(documents, "delete_file_from_drive", lambda **kwargs: None)
    monkeypatch.setattr(
        documents,
        "update_file_content_in_drive",
        lambda **kwargs: {"drive_file_id": kwargs["drive_file_id"], "web_view_link": "https://drive/new"},
    )

    monkeypatch.setattr(
        documents,
        "upload_file_to_drive",
        lambda **kwargs: {"drive_file_id": "drive123", "web_view_link": "https://drive/new"},
    )

    return TestClient(main.app)

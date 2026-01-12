def _login(client):
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_db(client):
    r = client.get("/health/db")
    assert r.status_code == 200


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_login_and_me(client):
    headers = _login(client)
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"


def test_non_admin_requires_whitelist(client, monkeypatch):
    import backend.main as main

    user = {
        "id": 2,
        "email": "staf@example.com",
        "password_hash": main.hash_password("Pass123!"),
        "role": "staf",
    }
    monkeypatch.setattr(main, "get_user_by_email", lambda email: user if email == user["email"] else None)
    monkeypatch.setattr(main, "is_email_allowed", lambda email: False)

    r = client.post("/api/auth/login", json={"email": user["email"], "password": "Pass123!"})
    assert r.status_code == 403


def test_admin_create_staff_user(client, monkeypatch):
    import backend.main as main

    headers = _login(client)

    monkeypatch.setattr(main, "get_user_by_email", lambda email: None)
    monkeypatch.setattr(main, "add_allowed_email", lambda email: {"email": email, "created_at": "2026-01-01T00:00:00"})
    monkeypatch.setattr(
        main,
        "create_user",
        lambda email, password_hash, role: {"id": 3, "email": email, "role": role, "created_at": "2026-01-01T00:00:00"},
    )

    r = client.post(
        "/api/admin/users",
        headers=headers,
        json={"email": "newstaf@example.com", "password": "Pass123!", "role": "staf"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "created"
    assert r.json()["user"]["role"] == "staf"


def test_admin_create_staff_user_idempotent_update(client, monkeypatch):
    import backend.main as main

    headers = _login(client)

    existing = {"id": 3, "email": "newstaf@example.com", "password_hash": "x", "role": "staf"}
    monkeypatch.setattr(main, "get_user_by_email", lambda email: existing if email == existing["email"] else None)
    monkeypatch.setattr(main, "add_allowed_email", lambda email: {"email": email, "created_at": "2026-01-01T00:00:00"})
    monkeypatch.setattr(
        main,
        "update_user_credentials_by_email",
        lambda **kwargs: {"id": 3, "email": kwargs["email"], "role": kwargs["role"], "created_at": "2026-01-01T00:00:00"},
    )

    r = client.post(
        "/api/admin/users",
        headers=headers,
        json={"email": "newstaf@example.com", "password": "NewPass123!", "role": "sekretaria"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "updated"
    assert r.json()["user"]["role"] == "sekretaria"


def test_list_documents_requires_auth(client):
    r = client.get("/api/documents")
    assert r.status_code == 401


def test_forbidden_role(client):
    from backend.app.auth import create_access_token
    import backend.app.documents as documents

    token = create_access_token(user_id=2, email="staf@example.com", role="staf")
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure the document is owned by someone else.
    documents.get_document_uploader_id = lambda doc_id: 1

    r = client.delete("/api/documents/1", headers=headers)
    assert r.status_code == 403


def test_delete_document_admin(client):
    headers = _login(client)
    r = client.delete("/api/documents/1", headers=headers)
    assert r.status_code == 200


def test_replace_file_requires_multipart(client):
    headers = _login(client)
    r = client.put("/api/documents/1/file", headers=headers)
    assert r.status_code == 400


def test_archive_document(client):
    headers = _login(client)
    r = client.patch("/api/documents/1/archive", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "archived"


def test_create_document_multipart(client):
    headers = _login(client)

    files = {
        "file": ("test.pdf", b"%PDF-1.4\n%test\n", "application/pdf"),
    }
    data = {
        "title": "Dokument test",
        "category": "request",
        "description": "pershkrim",
        "tags": "tag1,tag2",
    }
    r = client.post("/api/documents", headers=headers, data=data, files=files)
    assert r.status_code == 201

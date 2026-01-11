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


def test_list_documents_requires_auth(client):
    r = client.get("/api/documents")
    assert r.status_code == 401


def test_forbidden_role(client):
    from backend.app.auth import create_access_token

    token = create_access_token(user_id=2, email="staf@example.com", role="staf")
    headers = {"Authorization": f"Bearer {token}"}

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

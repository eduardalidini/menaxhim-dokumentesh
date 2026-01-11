from __future__ import annotations

from .config import get_database_url


def _normalize_database_url(database_url: str) -> str:
    # Allow .env to contain async style URLs (postgresql+asyncpg://) while
    # using psycopg directly.
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


def get_conninfo() -> str:
    # psycopg accepts libpq-style DSN URLs.
    return _normalize_database_url(get_database_url())


def _connect():
    import psycopg

    # Prevent "spinning" requests when the DB is unreachable.
    # connect_timeout is in seconds.
    return psycopg.connect(get_conninfo(), connect_timeout=5)


def init_db() -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS academic_documents (
        id BIGSERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NULL,
        category VARCHAR(100) NOT NULL,
        tags TEXT NULL,
        file_type VARCHAR(100) NOT NULL,
        drive_file_id TEXT UNIQUE NOT NULL,
        web_view_link TEXT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        ai_summary TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_academic_documents_title ON academic_documents (title);
    CREATE INDEX IF NOT EXISTS idx_academic_documents_category ON academic_documents (category);
    CREATE INDEX IF NOT EXISTS idx_academic_documents_status ON academic_documents (status);

    CREATE TABLE IF NOT EXISTS drive_oauth_tokens (
        id SMALLINT PRIMARY KEY,
        refresh_token TEXT NOT NULL,
        token_uri TEXT NOT NULL,
        client_id TEXT NOT NULL,
        client_secret TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS drive_oauth_states (
        state TEXT PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()


def scalar(sql: str) -> object:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                return None
            return row[0]


def fetchone(sql: str, params: tuple[object, ...] = ()) -> tuple[object, ...] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row


def execute_returning(sql: str, params: tuple[object, ...] = ()) -> tuple[object, ...] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
        return row


def execute(sql: str, params: tuple[object, ...] = ()) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


def get_user_by_email(email: str) -> dict | None:
    row = fetchone(
        "SELECT id, username, password_hash, role, created_at FROM users WHERE username = %s",
        (email,),
    )
    if not row:
        return None
    return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3], "created_at": row[4]}


def create_user(email: str, password_hash: str, role: str) -> dict:
    row = execute_returning(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id, username, role, created_at",
        (email, password_hash, role),
    )
    if not row:
        raise RuntimeError("Failed to create user")
    return {"id": row[0], "email": row[1], "role": row[2], "created_at": row[3]}


def _row_to_document(row: tuple[object, ...]) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "category": row[3],
        "tags": row[4],
        "file_type": row[5],
        "drive_file_id": row[6],
        "web_view_link": row[7],
        "status": row[8],
        "ai_summary": row[9],
        "created_at": row[10].isoformat() if hasattr(row[10], "isoformat") else row[10],
        "updated_at": row[11].isoformat() if hasattr(row[11], "isoformat") else row[11],
    }


def get_document_by_id(doc_id: int) -> dict | None:
    row = fetchone(
        """
        SELECT id, title, description, category, tags, file_type, drive_file_id, web_view_link,
               status, ai_summary, created_at, updated_at
        FROM academic_documents
        WHERE id = %s
        """,
        (doc_id,),
    )
    if not row:
        return None
    return _row_to_document(row)


def update_document_file_by_id(
    *,
    doc_id: int,
    file_type: str,
    web_view_link: str,
) -> dict | None:
    row = execute_returning(
        """
        UPDATE academic_documents
        SET file_type = %s, web_view_link = %s, updated_at = NOW()
        WHERE id = %s
        RETURNING id, title, description, category, tags, file_type, drive_file_id, web_view_link,
                  status, ai_summary, created_at, updated_at
        """,
        (file_type, web_view_link, doc_id),
    )
    if not row:
        return None
    return _row_to_document(row)


def list_documents_rows(
    *,
    query: str | None,
    category: str | None,
    status: str | None,
    from_dt,
    to_dt,
    page: int,
    page_size: int,
) -> list[dict]:
    import psycopg

    where = []
    params: list[object] = []

    if query:
        where.append("title ILIKE %s")
        params.append(f"%{query}%")
    if category:
        where.append("category = %s")
        params.append(category)
    if status:
        where.append("status = %s")
        params.append(status)
    if from_dt is not None:
        where.append("created_at >= %s")
        params.append(from_dt)
    if to_dt is not None:
        where.append("created_at <= %s")
        params.append(to_dt)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    offset = (page - 1) * page_size

    sql = (
        """
        SELECT id, title, description, category, tags, file_type, drive_file_id, web_view_link,
               status, ai_summary, created_at, updated_at
        FROM academic_documents
        """
        + where_sql
        + " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    )
    params.extend([page_size, offset])

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
    return [_row_to_document(r) for r in rows]


def create_document_row(
    *,
    title: str,
    category: str,
    description: str | None,
    tags: str | None,
    file_type: str,
    drive_file_id: str,
    web_view_link: str,
) -> dict:
    row = execute_returning(
        """
        INSERT INTO academic_documents
          (title, description, category, tags, file_type, drive_file_id, web_view_link, status, updated_at)
        VALUES
          (%s, %s, %s, %s, %s, %s, %s, 'active', NOW())
        RETURNING id, title, description, category, tags, file_type, drive_file_id, web_view_link,
                  status, ai_summary, created_at, updated_at
        """,
        (title, description, category, tags, file_type, drive_file_id, web_view_link),
    )
    if not row:
        raise RuntimeError("Failed to create document")
    return _row_to_document(row)


def update_document_by_id(
    *,
    doc_id: int,
    title: str | None,
    category: str | None,
    description: str | None,
    tags: str | None,
) -> dict | None:
    sets = []
    params: list[object] = []

    if title is not None:
        sets.append("title = %s")
        params.append(title)
    if category is not None:
        sets.append("category = %s")
        params.append(category)
    if description is not None:
        sets.append("description = %s")
        params.append(description)
    if tags is not None:
        sets.append("tags = %s")
        params.append(tags)

    if not sets:
        return get_document_by_id(doc_id)

    params.append(doc_id)
    row = execute_returning(
        """
        UPDATE academic_documents
        SET {sets}, updated_at = NOW()
        WHERE id = %s
        RETURNING id, title, description, category, tags, file_type, drive_file_id, web_view_link,
                  status, ai_summary, created_at, updated_at
        """.format(sets=", ".join(sets)),
        tuple(params),
    )
    if not row:
        return None
    return _row_to_document(row)


def archive_document_by_id(doc_id: int) -> dict | None:
    row = execute_returning(
        """
        UPDATE academic_documents
        SET status = 'archived', updated_at = NOW()
        WHERE id = %s
        RETURNING id, title, description, category, tags, file_type, drive_file_id, web_view_link,
                  status, ai_summary, created_at, updated_at
        """,
        (doc_id,),
    )
    if not row:
        return None
    return _row_to_document(row)


def delete_document_by_id(doc_id: int) -> bool:
    row = execute_returning("DELETE FROM academic_documents WHERE id = %s RETURNING id", (doc_id,))
    return bool(row)


def upsert_drive_oauth_token(*, refresh_token: str, token_uri: str, client_id: str, client_secret: str) -> None:
    execute(
        """
        INSERT INTO drive_oauth_tokens (id, refresh_token, token_uri, client_id, client_secret)
        VALUES (1, %s, %s, %s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            refresh_token = EXCLUDED.refresh_token,
            token_uri = EXCLUDED.token_uri,
            client_id = EXCLUDED.client_id,
            client_secret = EXCLUDED.client_secret,
            updated_at = NOW()
        """,
        (refresh_token, token_uri, client_id, client_secret),
    )


def get_drive_oauth_token() -> dict | None:
    row = fetchone(
        """
        SELECT refresh_token, token_uri, client_id, client_secret
        FROM drive_oauth_tokens
        WHERE id = 1
        """
    )
    if not row:
        return None
    return {"refresh_token": row[0], "token_uri": row[1], "client_id": row[2], "client_secret": row[3]}


def create_drive_oauth_state(state: str) -> None:
    execute(
        "INSERT INTO drive_oauth_states (state) VALUES (%s) ON CONFLICT (state) DO NOTHING",
        (state,),
    )


def consume_drive_oauth_state(state: str) -> bool:
    row = execute_returning("DELETE FROM drive_oauth_states WHERE state = %s RETURNING state", (state,))
    return bool(row)

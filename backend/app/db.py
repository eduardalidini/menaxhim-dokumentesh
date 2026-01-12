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

    CREATE TABLE IF NOT EXISTS allowed_emails (
        email VARCHAR(255) PRIMARY KEY,
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
        uploaded_by_user_id BIGINT NULL,
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

    CREATE TABLE IF NOT EXISTS drive_oauth_tokens_by_user (
        user_id BIGINT PRIMARY KEY,
        refresh_token TEXT NOT NULL,
        token_uri TEXT NOT NULL,
        client_id TEXT NOT NULL,
        client_secret TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_drive_oauth_tokens_by_user_user
            FOREIGN KEY (user_id) REFERENCES users (id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS drive_oauth_states (
        state TEXT PRIMARY KEY,
        token TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    # Add migration for existing drive_oauth_states table
    migration = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'drive_oauth_states') THEN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'drive_oauth_states' AND column_name = 'token') THEN
                ALTER TABLE drive_oauth_states ADD COLUMN token TEXT NULL;
            END IF;
        END IF;
    END $$;
    """

    # Add migration for existing academic_documents table
    migration_documents = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'academic_documents') THEN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_name = 'academic_documents' AND column_name = 'uploaded_by_user_id') THEN
                ALTER TABLE academic_documents ADD COLUMN uploaded_by_user_id BIGINT NULL;
            END IF;
        END IF;
    END $$;
    """

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.execute(migration)
            cur.execute(migration_documents)
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


def update_user_credentials_by_email(*, email: str, password_hash: str, role: str) -> dict | None:
    row = execute_returning(
        """
        UPDATE users
        SET password_hash = %s,
            role = %s
        WHERE username = %s
        RETURNING id, username, role, created_at
        """,
        (password_hash, role, email),
    )
    if not row:
        return None
    return {"id": row[0], "email": row[1], "role": row[2], "created_at": row[3]}


def list_allowed_emails() -> list[dict]:
    rows = []
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email, created_at FROM allowed_emails ORDER BY created_at DESC")
            rows = cur.fetchall() or []
    return [
        {
            "email": r[0],
            "created_at": r[1].isoformat() if hasattr(r[1], "isoformat") else r[1],
        }
        for r in rows
    ]


def add_allowed_email(email: str) -> dict:
    row = execute_returning(
        "INSERT INTO allowed_emails (email) VALUES (%s) ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email RETURNING email, created_at",
        (email,),
    )
    if not row:
        raise RuntimeError("Failed to add allowed email")
    return {"email": row[0], "created_at": row[1].isoformat() if hasattr(row[1], "isoformat") else row[1]}


def remove_allowed_email(email: str) -> bool:
    row = execute_returning("DELETE FROM allowed_emails WHERE email = %s RETURNING email", (email,))
    return bool(row)


def is_email_allowed(email: str) -> bool:
    row = fetchone("SELECT 1 FROM allowed_emails WHERE email = %s", (email,))
    return bool(row)


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
        "uploaded_by_email": row[8],
        "status": row[9],
        "ai_summary": row[10],
        "created_at": row[11].isoformat() if hasattr(row[11], "isoformat") else row[11],
        "updated_at": row[12].isoformat() if hasattr(row[12], "isoformat") else row[12],
    }


def get_document_by_id(doc_id: int) -> dict | None:
    row = fetchone(
        """
        SELECT d.id, d.title, d.description, d.category, d.tags, d.file_type, d.drive_file_id, d.web_view_link,
               u.username AS uploaded_by_email,
               d.status, d.ai_summary, d.created_at, d.updated_at
        FROM academic_documents d
        LEFT JOIN users u ON u.id = d.uploaded_by_user_id
        WHERE d.id = %s
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
        RETURNING id
        """,
        (file_type, web_view_link, doc_id),
    )
    if not row:
        return None
    return get_document_by_id(doc_id)


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
        SELECT d.id, d.title, d.description, d.category, d.tags, d.file_type, d.drive_file_id, d.web_view_link,
               u.username AS uploaded_by_email,
               d.status, d.ai_summary, d.created_at, d.updated_at
        FROM academic_documents d
        LEFT JOIN users u ON u.id = d.uploaded_by_user_id
        """
        + where_sql.replace("created_at", "d.created_at")
        + " ORDER BY d.created_at DESC LIMIT %s OFFSET %s"
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
    uploaded_by_user_id: int | None,
) -> dict:
    row = execute_returning(
        """
        INSERT INTO academic_documents
          (title, description, category, tags, file_type, drive_file_id, web_view_link, uploaded_by_user_id, status, updated_at)
        VALUES
          (%s, %s, %s, %s, %s, %s, %s, %s, 'active', NOW())
        RETURNING id
        """,
        (title, description, category, tags, file_type, drive_file_id, web_view_link, uploaded_by_user_id),
    )
    if not row:
        raise RuntimeError("Failed to create document")
    return get_document_by_id(int(row[0]))


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
        RETURNING id
        """.format(sets=", ".join(sets)),
        tuple(params),
    )
    if not row:
        return None
    return get_document_by_id(doc_id)


def archive_document_by_id(doc_id: int) -> dict | None:
    row = execute_returning(
        """
        UPDATE academic_documents
        SET status = 'archived', updated_at = NOW()
        WHERE id = %s
        RETURNING id
        """,
        (doc_id,),
    )
    if not row:
        return None
    return get_document_by_id(doc_id)


def delete_document_by_id(doc_id: int) -> bool:
    row = execute_returning("DELETE FROM academic_documents WHERE id = %s RETURNING id", (doc_id,))
    return bool(row)


def get_document_uploader_id(doc_id: int) -> int | None:
    row = fetchone("SELECT uploaded_by_user_id FROM academic_documents WHERE id = %s", (doc_id,))
    if not row:
        return None
    value = row[0]
    return int(value) if value is not None else None


def set_document_ai_summary(*, doc_id: int, ai_summary: str) -> dict | None:
    row = execute_returning(
        """
        UPDATE academic_documents
        SET ai_summary = %s, updated_at = NOW()
        WHERE id = %s
        RETURNING id
        """,
        (ai_summary, doc_id),
    )
    if not row:
        return None
    return get_document_by_id(doc_id)


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


def get_drive_oauth_token_meta() -> dict | None:
    row = fetchone(
        """
        SELECT refresh_token, token_uri, client_id, client_secret, created_at, updated_at
        FROM drive_oauth_tokens
        WHERE id = 1
        """
    )
    if not row:
        return None
    return {
        "refresh_token": row[0],
        "token_uri": row[1],
        "client_id": row[2],
        "client_secret": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


def delete_drive_oauth_token() -> bool:
    row = execute_returning("DELETE FROM drive_oauth_tokens WHERE id = 1 RETURNING id", ())
    return bool(row)


def upsert_drive_oauth_token_for_user(
    *,
    user_id: int,
    refresh_token: str,
    token_uri: str,
    client_id: str,
    client_secret: str,
) -> None:
    execute(
        """
        INSERT INTO drive_oauth_tokens_by_user (user_id, refresh_token, token_uri, client_id, client_secret)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            refresh_token = EXCLUDED.refresh_token,
            token_uri = EXCLUDED.token_uri,
            client_id = EXCLUDED.client_id,
            client_secret = EXCLUDED.client_secret,
            updated_at = NOW()
        """,
        (user_id, refresh_token, token_uri, client_id, client_secret),
    )


def get_drive_oauth_token_for_user(user_id: int) -> dict | None:
    row = fetchone(
        """
        SELECT refresh_token, token_uri, client_id, client_secret
        FROM drive_oauth_tokens_by_user
        WHERE user_id = %s
        """,
        (user_id,),
    )
    if not row:
        return None
    return {"refresh_token": row[0], "token_uri": row[1], "client_id": row[2], "client_secret": row[3]}


def get_drive_oauth_token_meta_for_user(user_id: int) -> dict | None:
    row = fetchone(
        """
        SELECT refresh_token, token_uri, client_id, client_secret, created_at, updated_at
        FROM drive_oauth_tokens_by_user
        WHERE user_id = %s
        """,
        (user_id,),
    )
    if not row:
        return None
    return {
        "refresh_token": row[0],
        "token_uri": row[1],
        "client_id": row[2],
        "client_secret": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


def delete_drive_oauth_token_for_user(user_id: int) -> bool:
    row = execute_returning(
        "DELETE FROM drive_oauth_tokens_by_user WHERE user_id = %s RETURNING user_id",
        (user_id,),
    )
    return bool(row)


def create_drive_oauth_state(state: str) -> None:
    execute(
        "INSERT INTO drive_oauth_states (state) VALUES (%s) ON CONFLICT (state) DO NOTHING",
        (state,),
    )


def create_drive_oauth_state_with_token(state: str, token: str) -> None:
    execute(
        "INSERT INTO drive_oauth_states (state, token) VALUES (%s, %s) ON CONFLICT (state) DO UPDATE SET token = EXCLUDED.token",
        (state, token),
    )


def get_drive_oauth_state_with_token(state: str) -> dict | None:
    row = fetchone(
        "SELECT state, token, created_at FROM drive_oauth_states WHERE state = %s",
        (state,),
    )
    if not row:
        return None
    return {"state": row[0], "token": row[1], "created_at": row[2]}


def consume_drive_oauth_state(state: str) -> bool:
    row = execute_returning("DELETE FROM drive_oauth_states WHERE state = %s RETURNING state", (state,))
    return bool(row)

import os

from dotenv import load_dotenv


load_dotenv()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Create a .env file based on .env.example")
    return database_url


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is not set. Create a .env file based on .env.example")
    return secret


def get_jwt_expires_minutes() -> int:
    value = os.getenv("JWT_EXPIRES_MINUTES", "60")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError("JWT_EXPIRES_MINUTES must be an integer") from exc


def get_seed_admin_email() -> str | None:
    return os.getenv("SEED_ADMIN_EMAIL")


def get_seed_admin_password() -> str | None:
    return os.getenv("SEED_ADMIN_PASSWORD")


def get_drive_folder_id() -> str:
    folder_id = os.getenv("DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("DRIVE_FOLDER_ID is not set. Create a .env file based on .env.example")
    return folder_id


def get_google_oauth_client_json() -> str | None:
    return os.getenv("GOOGLE_OAUTH_CLIENT_JSON")


def get_public_base_url() -> str | None:
    # Public base URL of the deployed API, used to build OAuth redirect URI.
    # Example: https://my-api.example.com
    return os.getenv("PUBLIC_BASE_URL")

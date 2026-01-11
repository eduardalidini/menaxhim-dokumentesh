import time

import bcrypt
import jwt
from starlette.requests import Request

from .config import get_jwt_expires_minutes, get_jwt_secret


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, email: str, role: str) -> str:
    now = int(time.time())
    exp = now + int(get_jwt_expires_minutes()) * 60
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])


def get_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if not auth:
        return None
    parts = auth.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, value = parts
    if scheme.lower() != "bearer":
        return None
    return value.strip() or None


def require_auth(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise PermissionError("unauthorized")
    return user


def require_role(request: Request, allowed_roles: set[str]) -> dict:
    user = require_auth(request)
    role = user.get("role")
    if role not in allowed_roles:
        raise PermissionError("forbidden")
    return user

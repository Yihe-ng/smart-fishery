import hashlib
import hmac
import secrets

from fastapi import HTTPException, status

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 120000
PASSWORD_PREFIX = f"{PASSWORD_SCHEME}$"
TOKEN_PREFIX = "mock_token_"
REFRESH_TOKEN_PREFIX = "mock_refresh_token_"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_password: str) -> bool:
    if not stored_password:
        return False

    if not stored_password.startswith(PASSWORD_PREFIX):
        return hmac.compare_digest(stored_password, password)

    try:
        _, iteration_text, salt, expected_digest = stored_password.split("$", 3)
        iterations = int(iteration_text)
    except ValueError:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)


def needs_password_upgrade(stored_password: str) -> bool:
    return not stored_password.startswith(PASSWORD_PREFIX)


def create_access_token(user_name: str) -> str:
    return f"{TOKEN_PREFIX}{user_name}"


def create_refresh_token(user_name: str) -> str:
    return f"{REFRESH_TOKEN_PREFIX}{user_name}"


def extract_user_name_from_auth_header(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
        )

    token = authorization.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token.startswith(TOKEN_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证",
        )

    user_name = token[len(TOKEN_PREFIX) :].strip()
    if not user_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证",
        )

    return user_name

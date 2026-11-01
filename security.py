"""Passwords, JWT tokens and field-level encryption for sensitive notes."""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(subject: str, extra: dict | None = None) -> str:
    s = get_settings()
    minutes = int(s.get("auth.access_token_minutes", 60))
    payload = {
        "sub": subject,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, s.secret_key, algorithm=s.get("auth.algorithm", "HS256"))


def create_scoped_token(subject: str, scope: str, minutes: int, **claims) -> str:
    """Short-lived token for a narrow purpose (e.g. unlocking sensitive card sections)."""
    s = get_settings()
    payload = {
        "sub": subject,
        "scope": scope,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
        **claims,
    }
    return jwt.encode(payload, s.secret_key, algorithm=s.get("auth.algorithm", "HS256"))


def decode_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.secret_key, algorithms=[s.get("auth.algorithm", "HS256")])


def _fernet() -> Fernet:
    s = get_settings()
    key = s.field_encryption_key
    if not key:
        # Dev fallback: derive a stable key from SECRET_KEY (prod must set FIELD_ENCRYPTION_KEY)
        key = base64.urlsafe_b64encode(hashlib.sha256(s.secret_key.encode()).digest()).decode()
    return Fernet(key.encode())


def encrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    return "enc:" + _fernet().encrypt(value.encode()).decode()


def decrypt_text(value: str | None) -> str | None:
    if value is None or not value.startswith("enc:"):
        return value
    try:
        return _fernet().decrypt(value[4:].encode()).decode()
    except InvalidToken:
        return None

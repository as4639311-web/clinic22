from __future__ import annotations

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .core.config import get_settings
from .core.security import decode_token
from .db import get_db
from .models import AccessLog, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not_authenticated")
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_token")
    if payload.get("scope", "access") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_token")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user_not_found")
    return user


def unlocked_sections(
    x_unlock_token: str | None = Header(default=None),
    user: User = Depends(get_current_user),
) -> set[str]:
    """Locked sections (config privacy.locked_sections) need a short-lived unlock token."""
    if not x_unlock_token:
        return set()
    try:
        payload = decode_token(x_unlock_token)
    except jwt.PyJWTError:
        return set()
    if payload.get("scope") != "unlock" or payload.get("sub") != str(user.id):
        return set()
    return set(payload.get("sections", []))


def audit(db: Session, user_id: int, actor: str, action: str, section: str) -> None:
    if get_settings().get("privacy.audit_access", True):
        db.add(AccessLog(user_id=user_id, actor=actor, action=action, section=section))

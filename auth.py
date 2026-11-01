from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.security import create_access_token, hash_password, verify_password
from ..db import get_db
from ..deps import get_current_user
from ..models import MedicalHistory, User
from ..schemas import LoginIn, PrefsIn, RegisterIn
from ..serial import user_out

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("auth")


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    min_len = int(get_settings().get("auth.password_min_length", 8))
    if len(body.password) < min_len:
        raise HTTPException(422, "password_too_short")
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "email_taken")
    user = User(
        email=body.email.lower(), password_hash=hash_password(body.password), full_name=body.full_name,
        phone=body.phone, birth_date=body.birth_date, gender=body.gender, locale=body.locale,
        file_number=f"TW-{secrets.randbelow(900000) + 100000}",
    )
    db.add(user)
    db.flush()
    db.add(MedicalHistory(user_id=user.id))
    db.commit()
    log.info("user registered id=%s", user.id)
    return {"access_token": create_access_token(str(user.id)), "user": user_out(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        log.warning("failed login for %s", body.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    return {"access_token": create_access_token(str(user.id)), "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.patch("/me")
def update_me(body: PrefsIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    return user_out(user)

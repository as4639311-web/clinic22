from __future__ import annotations

from ..core.clock import utcnow

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db import get_db
from ..deps import audit, get_current_user
from ..models import CARD_SECTIONS, AccessLog, ShareGrant, Specialist, User
from ..schemas import ShareIn
from ..serial import iso_utc, specialist_out

router = APIRouter(prefix="/shares", tags=["sharing"])


def _out(g: ShareGrant) -> dict:
    active = not g.revoked and (g.expires_at is None or g.expires_at > utcnow())
    return {"id": g.id, "specialist": specialist_out(g.specialist), "sections": g.sections,
            "starts_at": iso_utc(g.starts_at), "expires_at": iso_utc(g.expires_at), "active": active}


@router.get("")
def list_shares(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ShareGrant).where(ShareGrant.user_id == user.id).order_by(ShareGrant.starts_at.desc()))
    return [_out(g) for g in rows]


@router.post("", status_code=201)
def create_share(body: ShareIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(Specialist, body.specialist_id):
        raise HTTPException(404, "specialist_not_found")
    bad = [s for s in body.sections if s not in CARD_SECTIONS]
    if bad:
        raise HTTPException(422, f"unknown_sections:{','.join(bad)}")
    now = utcnow()
    expires = {
        "session": now + timedelta(days=1),
        "month": now + timedelta(days=int(get_settings().get("privacy.default_share_days", 30))),
        "until_revoked": None,
    }[body.duration]
    g = ShareGrant(user_id=user.id, specialist_id=body.specialist_id, sections=body.sections, expires_at=expires)
    db.add(g)
    audit(db, user.id, "self", "share", ",".join(body.sections))
    db.commit()
    db.refresh(g)
    return _out(g)


@router.post("/{share_id}/revoke")
def revoke(share_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.get(ShareGrant, share_id)
    if not g or g.user_id != user.id:
        raise HTTPException(404, "share_not_found")
    g.revoked = True
    audit(db, user.id, "self", "revoke", ",".join(g.sections))
    db.commit()
    return _out(g)


@router.get("/access-log")
def access_log(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AccessLog).where(AccessLog.user_id == user.id).order_by(AccessLog.at.desc()).limit(100))
    return [{"actor": r.actor, "action": r.action, "section": r.section, "at": iso_utc(r.at)} for r in rows]

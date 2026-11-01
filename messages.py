from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.security import decrypt_text, encrypt_text
from ..db import get_db
from ..deps import get_current_user
from ..models import Appointment, Message, Specialist, User
from ..schemas import MessageIn
from ..serial import iso_utc, specialist_out

router = APIRouter(prefix="/messages", tags=["messages"])


def _out(m: Message) -> dict:
    return {"id": m.id, "sender": m.sender, "body": decrypt_text(m.body), "created_at": iso_utc(m.created_at), "read": m.read}


def _can_message(db: Session, user: User, specialist_id: int) -> bool:
    """Secure messaging is open only with specialists the user has booked."""
    return db.scalar(select(Appointment.id).where(Appointment.user_id == user.id, Appointment.specialist_id == specialist_id)) is not None


@router.get("/threads")
def threads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sp_ids = {a.specialist_id for a in db.scalars(select(Appointment).where(Appointment.user_id == user.id))}
    out = []
    for sid in sp_ids:
        sp = db.get(Specialist, sid)
        last = db.scalars(select(Message).where(Message.user_id == user.id, Message.specialist_id == sid)
                          .order_by(Message.created_at.desc())).first()
        unread = len(db.scalars(select(Message).where(Message.user_id == user.id, Message.specialist_id == sid,
                                                      Message.sender == "specialist", Message.read.is_(False))).all())
        out.append({"specialist": specialist_out(sp), "last": _out(last) if last else None, "unread": unread})
    out.sort(key=lambda t: (t["last"] or {}).get("created_at") or "", reverse=True)
    return out


@router.get("/{specialist_id}")
def thread(specialist_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _can_message(db, user, specialist_id):
        raise HTTPException(403, "no_relationship")
    rows = list(db.scalars(select(Message).where(Message.user_id == user.id, Message.specialist_id == specialist_id)
                           .order_by(Message.created_at)))
    for m in rows:
        if m.sender == "specialist":
            m.read = True
    db.commit()
    return [_out(m) for m in rows]


@router.post("", status_code=201)
def send(body: MessageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _can_message(db, user, body.specialist_id):
        raise HTTPException(403, "no_relationship")
    m = Message(user_id=user.id, specialist_id=body.specialist_id, sender="user", body=encrypt_text(body.body))
    db.add(m)
    db.commit()
    return _out(m)

"""Notification centre + smart reminders derived from the user's state."""
from __future__ import annotations

from ..core.clock import utcnow

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Appointment, Measurement, Notification, User
from ..serial import bi, iso_utc

router = APIRouter(prefix="/notifications", tags=["notifications"])


def smart_reminders(db: Session, user: User) -> list[dict]:
    out = []
    now = datetime.now()
    soon = db.scalars(select(Appointment).where(
        Appointment.user_id == user.id, Appointment.status == "booked",
        Appointment.starts_at >= now, Appointment.starts_at <= now + timedelta(hours=24),
    )).all()
    for a in soon:
        mins = int((a.starts_at - now).total_seconds() // 60)
        out.append({"kind": "appointment", "priority": "high" if mins <= 60 else "normal",
                    "title": bi("موعدك قريب", "Your appointment is coming up"),
                    "body": bi(f"مع {a.specialist.name_ar} الساعة {a.starts_at:%H:%M}",
                               f"With {a.specialist.name_en} at {a.starts_at:%H:%M}"),
                    "ref": {"appointment_id": a.id}})
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)  # measurements are stored in UTC
    did_checkin = db.scalars(select(Measurement).where(
        Measurement.user_id == user.id, Measurement.kind == "mood", Measurement.recorded_at >= start)).first()
    if not did_checkin:
        out.append({"kind": "checkin", "priority": "low",
                    "title": bi("كيف حالك اليوم؟", "How are you today?"),
                    "body": bi("فحص سريع في 10 ثوانٍ", "A 10-second check-in"), "ref": None})
    return out


@router.get("")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.created_at.desc()).limit(50))
    return {
        "smart": smart_reminders(db, user),
        "items": [{"id": n.id, "kind": n.kind, "title": bi(n.title_ar, n.title_en), "body": bi(n.body_ar, n.body_en),
                   "created_at": iso_utc(n.created_at), "read": n.read} for n in rows],
    }


@router.post("/read-all")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for n in db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read.is_(False))):
        n.read = True
    db.commit()
    return {"ok": True}

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..models import Appointment, Specialist
from ..serial import specialist_out

router = APIRouter(prefix="/specialists", tags=["specialists"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_specialists(
    service: str | None = None,
    gender: str | None = None,
    language: str | None = None,
    mode: str | None = None,
    db: Session = Depends(get_db),
):
    q = select(Specialist)
    if service:
        q = q.where(Specialist.service == service)
    if gender:
        q = q.where(Specialist.gender == gender)
    rows = db.scalars(q.order_by(Specialist.rating.desc())).all()
    if language:
        rows = [r for r in rows if language in r.languages]
    if mode:
        rows = [r for r in rows if mode in r.modes]
    out = []
    for s in rows:
        d = specialist_out(s)
        d["next_slot"] = next((sl for day in _days(1, 7) for sl in free_slots(db, s.id, day)), None)
        out.append(d)
    # soonest available first, then rating
    out.sort(key=lambda d: (d["next_slot"] or "9999", -d["rating"]))
    return out


@router.get("/{specialist_id}")
def get_specialist(specialist_id: int, db: Session = Depends(get_db)):
    s = db.get(Specialist, specialist_id)
    if not s:
        raise HTTPException(404, "specialist_not_found")
    return specialist_out(s)


@router.get("/{specialist_id}/availability")
def availability(specialist_id: int, start: date | None = None, days: int = Query(7, ge=1, le=31), db: Session = Depends(get_db)):
    if not db.get(Specialist, specialist_id):
        raise HTTPException(404, "specialist_not_found")
    start = start or date.today()
    return [{"date": d.isoformat(), "slots": free_slots(db, specialist_id, d)} for d in (start + timedelta(i) for i in range(days))]


def _days(offset: int, count: int):
    return [date.today() + timedelta(days=offset + i) for i in range(count)]


def free_slots(db: Session, specialist_id: int, day: date) -> list[str]:
    s = get_settings()
    step = int(s.get("booking.slot_minutes", 45))
    h0, m0 = map(int, s.get("booking.work_hours.start", "09:00").split(":"))
    h1, m1 = map(int, s.get("booking.work_hours.end", "21:00").split(":"))
    if day.weekday() == 4:  # Friday: shorter day
        h0, m0 = 14, 0
    start, end = datetime.combine(day, time(h0, m0)), datetime.combine(day, time(h1, m1))
    taken = {
        a.starts_at
        for a in db.scalars(
            select(Appointment).where(
                Appointment.specialist_id == specialist_id,
                Appointment.status == "booked",
                Appointment.starts_at >= start,
                Appointment.starts_at < end,
            )
        )
    }
    slots, t = [], start
    now = datetime.now()
    while t + timedelta(minutes=step) <= end:
        if t not in taken and t > now:
            slots.append(t.isoformat(timespec="minutes"))
        t += timedelta(minutes=step)
    return slots

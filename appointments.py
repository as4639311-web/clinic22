from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..db import get_db
from ..deps import get_current_user
from ..models import Appointment, Notification, ShareGrant, Specialist, User
from ..schemas import AppointmentIn, RescheduleIn
from ..serial import appointment_out
from .specialists import free_slots

router = APIRouter(prefix="/appointments", tags=["appointments"])
log = get_logger("appointments")


@router.get("")
def list_appointments(scope: str = "upcoming", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now()
    q = select(Appointment).where(Appointment.user_id == user.id)
    if scope == "upcoming":
        q = q.where(Appointment.starts_at >= now - timedelta(hours=1), Appointment.status == "booked").order_by(Appointment.starts_at)
    else:
        q = q.where((Appointment.starts_at < now - timedelta(hours=1)) | (Appointment.status != "booked")).order_by(Appointment.starts_at.desc())
    return [appointment_out(a) for a in db.scalars(q)]


@router.get("/{appointment_id}")
def get_appointment(appointment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return appointment_out(_own(db, user, appointment_id))


@router.post("", status_code=201)
def book(body: AppointmentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sp = db.get(Specialist, body.specialist_id)
    if not sp:
        raise HTTPException(404, "specialist_not_found")
    if body.mode not in sp.modes:
        raise HTTPException(422, "mode_not_offered")
    starts = body.starts_at.replace(tzinfo=None, second=0, microsecond=0)
    if starts.isoformat(timespec="minutes") not in free_slots(db, sp.id, starts.date()):
        raise HTTPException(409, "slot_unavailable")
    appt = Appointment(
        user_id=user.id, specialist_id=sp.id, service=sp.service, starts_at=starts, mode=body.mode,
        reason=body.reason, shared_sections=body.shared_sections,
    )
    db.add(appt)
    if body.shared_sections:
        db.add(ShareGrant(user_id=user.id, specialist_id=sp.id, sections=body.shared_sections,
                          expires_at=starts + timedelta(days=1)))
    db.add(Notification(
        user_id=user.id, kind="appointment",
        title_ar="تم تأكيد موعدك", title_en="Your appointment is confirmed",
        body_ar=f"مع {sp.name_ar} — {starts:%Y-%m-%d %H:%M}", body_en=f"With {sp.name_en} — {starts:%Y-%m-%d %H:%M}",
    ))
    db.commit()
    db.refresh(appt)
    log.info("appointment booked id=%s user=%s specialist=%s", appt.id, user.id, sp.id)
    return appointment_out(appt)


@router.post("/{appointment_id}/cancel")
def cancel(appointment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = _own(db, user, appointment_id)
    if appt.status != "booked":
        raise HTTPException(409, "not_cancellable")
    appt.status = "cancelled"
    db.commit()
    return appointment_out(appt)


@router.post("/{appointment_id}/reschedule")
def reschedule(appointment_id: int, body: RescheduleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = _own(db, user, appointment_id)
    if appt.status != "booked":
        raise HTTPException(409, "not_reschedulable")
    starts = body.starts_at.replace(tzinfo=None, second=0, microsecond=0)
    if starts.isoformat(timespec="minutes") not in free_slots(db, appt.specialist_id, starts.date()):
        raise HTTPException(409, "slot_unavailable")
    appt.starts_at = starts
    db.commit()
    return appointment_out(appt)


def _own(db: Session, user: User, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if not appt or appt.user_id != user.id:
        raise HTTPException(404, "appointment_not_found")
    return appt

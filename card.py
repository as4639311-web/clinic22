"""The personal card: profile, indicators, results, goals, history, timeline."""
from __future__ import annotations

from ..core.clock import utcnow

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import create_scoped_token, verify_password
from ..db import get_db
from ..deps import audit, get_current_user, unlocked_sections
from ..models import Appointment, Assessment, Goal, MedicalHistory, Measurement, ShareGrant, User
from ..schemas import CheckinIn, GoalIn, GoalProgressIn, MeasurementIn, UnlockIn
from ..serial import appointment_out, assessment_out, bi, goal_out, iso, specialist_out, trend_of, user_out, iso_utc

router = APIRouter(prefix="/card", tags=["card"])

HEADLINE = {  # which result headlines each indicator
    "mental": "PHQ-9",
    "physical": "VO2 max",
    "nutrition": "Body fat",
}


def _locked(unlocked: set[str]) -> set[str]:
    return set(get_settings().get("privacy.locked_sections", [])) - unlocked


def _assessments(db: Session, user_id: int, domain: str | None = None) -> list[Assessment]:
    q = select(Assessment).where(Assessment.user_id == user_id)
    if domain:
        q = q.where(Assessment.domain == domain)
    return list(db.scalars(q.order_by(Assessment.taken_at.desc())))


def _with_prev(rows: list[Assessment]) -> list[dict]:
    out = []
    for i, a in enumerate(rows):
        prev = next((b for b in rows[i + 1:] if b.name_en == a.name_en), None)
        out.append(assessment_out(a, prev))
    return out


def _latest_per_name(rows: list[Assessment]) -> list[dict]:
    seen, out = set(), []
    for d in _with_prev(rows):
        if d["name"]["en"] not in seen:
            seen.add(d["name"]["en"])
            out.append(d)
    return out


def _indicator(db: Session, user: User, domain: str) -> dict:
    rows = [a for a in _assessments(db, user.id, domain) if a.name_en == HEADLINE[domain]]
    if not rows:
        return {"domain": domain, "empty": True}
    cur = rows[0]
    prev = rows[1] if len(rows) > 1 else None
    return {
        "domain": domain, "label": bi(cur.name_ar, cur.name_en), "value": cur.value, "unit": cur.unit,
        "trend": trend_of(cur.value, prev.value if prev else None, cur.lower_is_better),
        "updated_at": iso_utc(cur.taken_at), "spark": [a.value for a in reversed(rows[:8])],
    }


def _general_indicator(db: Session, user: User) -> dict:
    since = utcnow() - timedelta(days=14)
    moods = list(db.scalars(select(Measurement).where(
        Measurement.user_id == user.id, Measurement.kind == "mood", Measurement.recorded_at >= since
    ).order_by(Measurement.recorded_at)))
    if not moods:
        return {"domain": "general", "empty": True}
    cut = utcnow() - timedelta(days=7)
    recent = [m.value for m in moods if m.recorded_at >= cut] or [moods[-1].value]
    older = [m.value for m in moods if m.recorded_at < cut]
    avg = round(sum(recent) / len(recent), 1)
    old_avg = round(sum(older) / len(older), 1) if older else None
    return {
        "domain": "general", "label": {"ar": "متوسط المزاج", "en": "Mood average"}, "value": avg, "unit": "/5",
        "trend": trend_of(avg, old_avg, False), "updated_at": iso_utc(moods[-1].recorded_at),
        "spark": [m.value for m in moods[-8:]],
    }


@router.get("")
def get_card(user: User = Depends(get_current_user), unlocked: set[str] = Depends(unlocked_sections), db: Session = Depends(get_db)):
    locked = _locked(unlocked)
    indicators = []
    for d in ("mental", "physical", "nutrition"):
        indicators.append({"domain": d, "locked": True} if d in locked else _indicator(db, user, d))
    indicators.append(_general_indicator(db, user))

    upcoming = db.scalars(select(Appointment).where(
        Appointment.user_id == user.id, Appointment.status == "booked", Appointment.starts_at >= datetime.now()
    ).order_by(Appointment.starts_at)).first()

    results = [r for r in _latest_per_name(_assessments(db, user.id)) if r["domain"] not in locked][:5]
    goals = [goal_out(g) for g in db.scalars(select(Goal).where(Goal.user_id == user.id, Goal.status == "active"))
             if g.domain not in locked]
    h = user.history or MedicalHistory()
    shares = db.scalars(select(ShareGrant).where(ShareGrant.user_id == user.id, ShareGrant.revoked.is_(False))).all()
    active_shares = [
        {"specialist": specialist_out(s.specialist), "sections": s.sections, "expires_at": iso_utc(s.expires_at)}
        for s in shares if not s.expires_at or s.expires_at > utcnow()
    ]
    audit(db, user.id, "self", "view", "card")
    db.commit()
    return {
        "profile": user_out(user),
        "alerts": {"allergies": h.allergies or [], "blood_type": h.blood_type},
        "indicators": indicators,
        "locked_sections": sorted(locked),
        "next_appointment": appointment_out(upcoming) if upcoming and upcoming.service not in locked else
            ({"locked": True, "starts_at": iso(upcoming.starts_at)} if upcoming else None),
        "recent_results": results,
        "goals": goals,
        "history": _history_out(h),
        "active_shares": active_shares,
    }


@router.post("/unlock")
def unlock(body: UnlockIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Re-confirm identity (password here; biometric on device) to open locked sections for 5 minutes."""
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "invalid_credentials")
    token = create_scoped_token(str(user.id), "unlock", minutes=5, sections=body.sections)
    audit(db, user.id, "self", "unlock", ",".join(body.sections))
    db.commit()
    return {"unlock_token": token, "expires_in": 300}


@router.get("/results")
def results(domain: str | None = None, user: User = Depends(get_current_user),
            unlocked: set[str] = Depends(unlocked_sections), db: Session = Depends(get_db)):
    if domain and domain in _locked(unlocked):
        raise HTTPException(423, "section_locked")
    rows = [r for r in _with_prev(_assessments(db, user.id, domain)) if r["domain"] not in _locked(unlocked)]
    return rows


@router.get("/series")
def series(kind: str | None = None, assessment: str | None = None, days: int = Query(90, ge=7, le=730),
           user: User = Depends(get_current_user), unlocked: set[str] = Depends(unlocked_sections), db: Session = Depends(get_db)):
    since = utcnow() - timedelta(days=days)
    if assessment:
        rows = [a for a in _assessments(db, user.id) if a.name_en == assessment and a.taken_at >= since]
        if rows and rows[0].domain in _locked(unlocked):
            raise HTTPException(423, "section_locked")
        return [{"t": iso_utc(a.taken_at), "v": a.value} for a in reversed(rows)]
    if not kind:
        raise HTTPException(422, "kind_or_assessment_required")
    rows = db.scalars(select(Measurement).where(
        Measurement.user_id == user.id, Measurement.kind == kind, Measurement.recorded_at >= since
    ).order_by(Measurement.recorded_at))
    return [{"t": iso_utc(m.recorded_at), "v": m.value} for m in rows]


@router.post("/measurements", status_code=201)
def add_measurement(body: MeasurementIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = Measurement(user_id=user.id, kind=body.kind, value=body.value, recorded_at=body.recorded_at or utcnow())
    db.add(m)
    if body.kind == "weight":  # keep weight goals current
        for g in db.scalars(select(Goal).where(Goal.user_id == user.id, Goal.unit == "kg", Goal.status == "active")):
            g.current_value = body.value
    db.commit()
    return {"id": m.id, "kind": m.kind, "value": m.value, "recorded_at": iso_utc(m.recorded_at)}


@router.post("/checkin", status_code=201)
def checkin(body: CheckinIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The 10-second daily check-in: mood, energy, sleep."""
    t = utcnow()
    for kind, v in (("mood", body.mood), ("energy", body.energy), ("sleep_hours", body.sleep_hours)):
        db.add(Measurement(user_id=user.id, kind=kind, value=v, recorded_at=t))
    db.commit()
    return {"ok": True, "recorded_at": iso_utc(t)}


@router.get("/checkin/today")
def checkin_today(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    m = db.scalars(select(Measurement).where(
        Measurement.user_id == user.id, Measurement.kind == "mood", Measurement.recorded_at >= start
    )).first()
    return {"done": m is not None}


@router.get("/goals")
def goals(user: User = Depends(get_current_user), unlocked: set[str] = Depends(unlocked_sections), db: Session = Depends(get_db)):
    locked = _locked(unlocked)
    return [goal_out(g) for g in db.scalars(select(Goal).where(Goal.user_id == user.id)) if g.domain not in locked]


@router.post("/goals", status_code=201)
def add_goal(body: GoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = Goal(user_id=user.id, domain=body.domain, title_ar=body.title, title_en=body.title,
             start_value=body.start_value, target_value=body.target_value, current_value=body.start_value,
             unit=body.unit, target_date=body.target_date)
    db.add(g)
    db.commit()
    return goal_out(g)


@router.patch("/goals/{goal_id}")
def update_goal(goal_id: int, body: GoalProgressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.get(Goal, goal_id)
    if not g or g.user_id != user.id:
        raise HTTPException(404, "goal_not_found")
    g.current_value = body.current_value
    if goal_out(g)["progress"] >= 1:
        g.status = "achieved"
    db.commit()
    return goal_out(g)


@router.get("/timeline")
def timeline(domain: str | None = None, user: User = Depends(get_current_user),
             unlocked: set[str] = Depends(unlocked_sections), db: Session = Depends(get_db)):
    locked = _locked(unlocked)
    svc_domain = {"mental": "mental", "fitness": "physical", "sports_medicine": "physical", "nutrition": "nutrition", "education": "general"}
    events = []
    for a in db.scalars(select(Appointment).where(Appointment.user_id == user.id, Appointment.status == "completed")):
        dom = svc_domain.get(a.service, "general")
        if dom in locked:
            continue
        events.append({"type": "consultation", "domain": dom, "at": iso(a.starts_at),
                       "title": bi(f"جلسة مع {a.specialist.name_ar}", f"Session with {a.specialist.name_en}"),
                       "detail": appointment_out(a)["summary"]})
    for a in _assessments(db, user.id):
        if a.domain in locked:
            continue
        events.append({"type": "result", "domain": a.domain, "at": iso_utc(a.taken_at),
                       "title": bi(a.name_ar, a.name_en), "detail": f"{a.value:g} {a.unit}".strip()})
    for g in db.scalars(select(Goal).where(Goal.user_id == user.id, Goal.status == "achieved")):
        events.append({"type": "achievement", "domain": g.domain, "at": iso(g.target_date) if g.target_date else None,
                       "title": bi(g.title_ar, g.title_en), "detail": None})
    if domain:
        events = [e for e in events if e["domain"] == domain]
    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return events[:50]


def _history_out(h: MedicalHistory) -> dict:
    return {
        "blood_type": h.blood_type, "chronic_conditions": h.chronic_conditions or [], "medications": h.medications or [],
        "allergies": h.allergies or [], "surgeries": h.surgeries or [], "injuries": h.injuries or [],
        "family_history": h.family_history or [],
    }

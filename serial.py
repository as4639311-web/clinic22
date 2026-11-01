"""Model → JSON helpers. Bilingual fields are returned as {"ar": ..., "en": ...}."""
from __future__ import annotations

from datetime import date, datetime

from .core.config import get_settings
from .core.security import decrypt_text
from .models import Appointment, Assessment, Goal, Plan, PlanItem, Specialist, User


def bi(ar: str | None, en: str | None) -> dict:
    return {"ar": ar or en or "", "en": en or ar or ""}


def iso(v: datetime | date | None) -> str | None:
    return v.isoformat() if v else None


def age_of(birth: date | None) -> int | None:
    if not birth:
        return None
    t = date.today()
    return t.year - birth.year - ((t.month, t.day) < (birth.month, birth.day))


def user_out(u: User) -> dict:
    return {
        "id": u.id, "email": u.email, "phone": u.phone, "full_name": u.full_name,
        "birth_date": iso(u.birth_date), "age": age_of(u.birth_date), "gender": u.gender,
        "avatar_url": u.avatar_url, "locale": u.locale, "theme": u.theme, "file_number": u.file_number,
    }


def specialist_out(s: Specialist) -> dict:
    return {
        "id": s.id, "name": bi(s.name_ar, s.name_en), "title": bi(s.title_ar, s.title_en),
        "service": s.service, "gender": s.gender, "languages": s.languages, "modes": s.modes,
        "rating": s.rating, "years": s.years, "bio": bi(s.bio_ar, s.bio_en),
    }


def appointment_out(a: Appointment) -> dict:
    sensitive = a.service in get_settings().get("privacy.encrypted_services", [])
    return {
        "id": a.id, "service": a.service, "starts_at": iso(a.starts_at), "duration_min": a.duration_min,
        "mode": a.mode, "status": a.status, "reason": a.reason,
        "summary": decrypt_text(a.summary) if a.summary else None, "sensitive": sensitive,
        "shared_sections": a.shared_sections, "specialist": specialist_out(a.specialist),
    }


def trend_of(cur: float, prev: float | None, lower_is_better: bool) -> str:
    if prev is None or abs(cur - prev) < 1e-9:
        return "stable"
    better = cur < prev if lower_is_better else cur > prev
    return "improving" if better else "needs_attention"


def assessment_out(a: Assessment, prev: Assessment | None = None) -> dict:
    status = "normal"
    if a.range_low is not None and a.value < a.range_low:
        status = "low"
    elif a.range_high is not None and a.value > a.range_high:
        status = "high"
    return {
        "id": a.id, "domain": a.domain, "kind": a.kind, "name": bi(a.name_ar, a.name_en),
        "value": a.value, "unit": a.unit, "range": [a.range_low, a.range_high],
        "previous": prev.value if prev else None,
        "trend": trend_of(a.value, prev.value if prev else None, a.lower_is_better),
        "status": status, "taken_at": iso_utc(a.taken_at), "note": bi(a.note_ar, a.note_en) if (a.note_ar or a.note_en) else None,
    }


def goal_out(g: Goal) -> dict:
    span = g.target_value - g.start_value
    progress = 0.0 if span == 0 else max(0.0, min(1.0, (g.current_value - g.start_value) / span))
    return {
        "id": g.id, "domain": g.domain, "title": bi(g.title_ar, g.title_en),
        "start_value": g.start_value, "target_value": g.target_value, "current_value": g.current_value,
        "unit": g.unit, "target_date": iso(g.target_date), "status": g.status, "progress": round(progress, 3),
    }


def item_out(i: PlanItem) -> dict:
    return {
        "id": i.id, "weekday": i.weekday, "title": bi(i.title_ar, i.title_en),
        "detail": bi(i.detail_ar, i.detail_en), "duration_min": i.duration_min,
    }


def plan_out(p: Plan, with_items: bool = False) -> dict:
    out = {
        "id": p.id, "kind": p.kind, "title": bi(p.title_ar, p.title_en),
        "start_date": iso(p.start_date), "end_date": iso(p.end_date), "version": p.version,
        "status": p.status, "specialist": specialist_out(p.specialist) if p.specialist else None,
    }
    if with_items:
        out["items"] = [item_out(i) for i in sorted(p.items, key=lambda x: (x.weekday, x.id))]
    return out


def iso_utc(v: datetime | None) -> str | None:
    """For columns stored as naive UTC: mark them so clients convert to local time."""
    return v.isoformat() + "Z" if v else None

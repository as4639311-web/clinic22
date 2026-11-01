from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db import get_db
from ..deps import get_current_user
from ..models import Notification, Plan, PlanChangeRequest, PlanItem, PlanLog, User
from ..schemas import PlanChangeIn, PlanLogIn
from ..serial import item_out, plan_out

router = APIRouter(prefix="/plans", tags=["plans"])


def _own(db: Session, user: User, plan_id: int) -> Plan:
    p = db.get(Plan, plan_id)
    if not p or p.user_id != user.id:
        raise HTTPException(404, "plan_not_found")
    return p


def _adherence(db: Session, user: User, plan: Plan, start: date, end: date) -> float | None:
    """done items / scheduled items between start and end (inclusive)."""
    scheduled = 0
    d = max(start, plan.start_date)
    while d <= end:
        scheduled += sum(1 for i in plan.items if i.weekday == d.weekday())
        d += timedelta(days=1)
    if scheduled == 0:
        return None
    ids = [i.id for i in plan.items]
    done = len(db.scalars(select(PlanLog).where(
        PlanLog.user_id == user.id, PlanLog.item_id.in_(ids), PlanLog.done.is_(True),
        PlanLog.day >= start, PlanLog.day <= end,
    )).all())
    return round(min(1.0, done / scheduled), 2)


@router.get("")
def list_plans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    out = []
    for p in db.scalars(select(Plan).where(Plan.user_id == user.id).order_by(Plan.status, Plan.start_date.desc())):
        d = plan_out(p)
        d["adherence_week"] = _adherence(db, user, p, today - timedelta(days=6), today)
        out.append(d)
    return out


@router.get("/today")
def today_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Today's items across all active plans, with done state — feeds the Home screen."""
    today = date.today()
    tasks = []
    for p in db.scalars(select(Plan).where(Plan.user_id == user.id, Plan.status == "active")):
        for i in p.items:
            if i.weekday != today.weekday():
                continue
            log = db.scalar(select(PlanLog).where(PlanLog.item_id == i.id, PlanLog.day == today, PlanLog.user_id == user.id))
            tasks.append({**item_out(i), "plan_id": p.id, "plan_kind": p.kind, "done": bool(log and log.done)})
    return {"date": today.isoformat(), "tasks": tasks}


@router.get("/{plan_id}")
def get_plan(plan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _own(db, user, plan_id)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    logs = db.scalars(select(PlanLog).where(
        PlanLog.user_id == user.id, PlanLog.item_id.in_([i.id for i in p.items]),
        PlanLog.day >= week_start, PlanLog.done.is_(True),
    )).all()
    out = plan_out(p, with_items=True)
    out["done_this_week"] = [{"item_id": l.item_id, "day": l.day.isoformat()} for l in logs]
    weeks = []
    for w in range(5, -1, -1):  # last 6 weeks, oldest first
        end = today - timedelta(days=7 * w)
        weeks.append({"week_end": end.isoformat(), "adherence": _adherence(db, user, p, end - timedelta(days=6), end)})
    out["weekly_adherence"] = weeks
    threshold = float(get_settings().get("plans.low_adherence_threshold", 0.6))
    recent = [w["adherence"] for w in weeks[-2:] if w["adherence"] is not None]
    out["suggest_review"] = len(recent) == 2 and all(a < threshold for a in recent)
    return out


@router.post("/log")
def log_item(body: PlanLogIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(PlanItem, body.item_id)
    if not item or item.plan.user_id != user.id:
        raise HTTPException(404, "item_not_found")
    if body.day > date.today():
        raise HTTPException(422, "future_day")
    log = db.scalar(select(PlanLog).where(PlanLog.item_id == item.id, PlanLog.day == body.day, PlanLog.user_id == user.id))
    if log:
        log.done = body.done
    else:
        db.add(PlanLog(item_id=item.id, user_id=user.id, day=body.day, done=body.done))
    db.commit()
    return {"ok": True}


@router.post("/{plan_id}/change-request", status_code=201)
def change_request(plan_id: int, body: PlanChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _own(db, user, plan_id)
    db.add(PlanChangeRequest(plan_id=p.id, user_id=user.id, message=body.message))
    db.add(Notification(user_id=user.id, kind="plan",
                        title_ar="تم إرسال طلب التعديل", title_en="Change request sent",
                        body_ar=f"سيراجع أخصائيك «{p.title_ar}» قريباً", body_en=f"Your specialist will review “{p.title_en}” soon"))
    db.commit()
    return {"ok": True}

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Content
from ..serial import bi

router = APIRouter(prefix="/content", tags=["education"], dependencies=[Depends(get_current_user)])


def _out(c: Content, full: bool = False) -> dict:
    d = {"id": c.id, "service": c.service, "type": c.type, "title": bi(c.title_ar, c.title_en),
         "summary": bi(c.summary_ar, c.summary_en), "minutes": c.minutes}
    if full:
        d["body"] = bi(c.body_ar, c.body_en)
    return d


@router.get("")
def list_content(service: str | None = None, type: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = select(Content)
    if service:
        query = query.where(Content.service == service)
    if type:
        query = query.where(Content.type == type)
    rows = db.scalars(query.order_by(Content.id.desc())).all()
    if q:
        ql = q.lower()
        rows = [c for c in rows if ql in (c.title_ar + c.title_en + c.summary_ar + c.summary_en).lower()]
    return [_out(c) for c in rows]


@router.get("/{content_id}")
def get_content(content_id: int, db: Session = Depends(get_db)):
    c = db.get(Content, content_id)
    if not c:
        raise HTTPException(404, "content_not_found")
    return _out(c, full=True)

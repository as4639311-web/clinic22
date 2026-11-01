"""Database models — mirrors the personal-card data structure in docs/data-model.md."""
from __future__ import annotations

from .core.clock import utcnow

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

SERVICES = ("mental", "fitness", "sports_medicine", "nutrition", "education")
DOMAINS = ("mental", "physical", "nutrition", "general")
CARD_SECTIONS = ("profile", "history", "mental", "physical", "nutrition", "goals", "appointments", "plans")


def now() -> datetime:
    return utcnow()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(16))  # female | male
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    locale: Mapped[str] = mapped_column(String(5), default="ar")
    theme: Mapped[str] = mapped_column(String(10), default="system")  # light | dark | system
    file_number: Mapped[str] = mapped_column(String(20), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    history: Mapped["MedicalHistory | None"] = relationship(back_populates="user", uselist=False)


class Specialist(Base):
    __tablename__ = "specialists"
    id: Mapped[int] = mapped_column(primary_key=True)
    name_ar: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    title_ar: Mapped[str] = mapped_column(String(160))
    title_en: Mapped[str] = mapped_column(String(160))
    service: Mapped[str] = mapped_column(String(32), index=True)
    gender: Mapped[str] = mapped_column(String(16))
    languages: Mapped[list] = mapped_column(JSON, default=list)
    modes: Mapped[list] = mapped_column(JSON, default=list)  # in_person | video | audio
    rating: Mapped[float] = mapped_column(Float, default=4.8)
    years: Mapped[int] = mapped_column(Integer, default=5)
    bio_ar: Mapped[str] = mapped_column(Text, default="")
    bio_en: Mapped[str] = mapped_column(Text, default="")


class MedicalHistory(Base):
    __tablename__ = "medical_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    blood_type: Mapped[str | None] = mapped_column(String(4))
    chronic_conditions: Mapped[list] = mapped_column(JSON, default=list)
    medications: Mapped[list] = mapped_column(JSON, default=list)
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    surgeries: Mapped[list] = mapped_column(JSON, default=list)
    injuries: Mapped[list] = mapped_column(JSON, default=list)
    family_history: Mapped[list] = mapped_column(JSON, default=list)
    user: Mapped[User] = relationship(back_populates="history")


class Assessment(Base):
    """A result: psychological scale, fitness test, body composition, lab value."""
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    domain: Mapped[str] = mapped_column(String(16))  # mental | physical | nutrition | general
    kind: Mapped[str] = mapped_column(String(16))    # scale | test | lab | body
    name_ar: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="")
    range_low: Mapped[float | None] = mapped_column(Float)
    range_high: Mapped[float | None] = mapped_column(Float)
    lower_is_better: Mapped[bool] = mapped_column(Boolean, default=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    specialist_id: Mapped[int | None] = mapped_column(ForeignKey("specialists.id"))
    note_ar: Mapped[str | None] = mapped_column(Text)
    note_en: Mapped[str | None] = mapped_column(Text)


class Measurement(Base):
    """Frequent self/device readings: weight, sleep, mood, energy, steps."""
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    domain: Mapped[str] = mapped_column(String(16))
    title_ar: Mapped[str] = mapped_column(String(160))
    title_en: Mapped[str] = mapped_column(String(160))
    start_value: Mapped[float] = mapped_column(Float)
    target_value: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="")
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="active")


class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    specialist_id: Mapped[int] = mapped_column(ForeignKey("specialists.id"))
    service: Mapped[str] = mapped_column(String(32))
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_min: Mapped[int] = mapped_column(Integer, default=45)
    mode: Mapped[str] = mapped_column(String(16))  # in_person | video | audio
    status: Mapped[str] = mapped_column(String(16), default="booked")  # booked | completed | cancelled
    reason: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)  # encrypted for sensitive services
    shared_sections: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    specialist: Mapped[Specialist] = relationship()


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    specialist_id: Mapped[int | None] = mapped_column(ForeignKey("specialists.id"))
    kind: Mapped[str] = mapped_column(String(16))  # training | nutrition | mental
    title_ar: Mapped[str] = mapped_column(String(160))
    title_en: Mapped[str] = mapped_column(String(160))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | archived | pending_review
    specialist: Mapped[Specialist | None] = relationship()
    items: Mapped[list["PlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class PlanItem(Base):
    __tablename__ = "plan_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Monday ... 6 = Sunday
    title_ar: Mapped[str] = mapped_column(String(160))
    title_en: Mapped[str] = mapped_column(String(160))
    detail_ar: Mapped[str] = mapped_column(Text, default="")
    detail_en: Mapped[str] = mapped_column(Text, default="")
    duration_min: Mapped[int | None] = mapped_column(Integer)
    plan: Mapped[Plan] = relationship(back_populates="items")


class PlanLog(Base):
    __tablename__ = "plan_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("plan_items.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=True)


class PlanChangeRequest(Base):
    __tablename__ = "plan_change_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ShareGrant(Base):
    __tablename__ = "share_grants"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    specialist_id: Mapped[int] = mapped_column(ForeignKey("specialists.id"))
    sections: Mapped[list] = mapped_column(JSON, default=list)
    starts_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    specialist: Mapped[Specialist] = relationship()


class AccessLog(Base):
    __tablename__ = "access_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(40))
    section: Mapped[str] = mapped_column(String(40))
    at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    specialist_id: Mapped[int] = mapped_column(ForeignKey("specialists.id"), index=True)
    sender: Mapped[str] = mapped_column(String(16))  # user | specialist
    body: Mapped[str] = mapped_column(Text)  # encrypted at rest
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # appointment | plan | message | result
    title_ar: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[str] = mapped_column(String(200))
    body_ar: Mapped[str] = mapped_column(Text, default="")
    body_en: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class Content(Base):
    __tablename__ = "content"
    id: Mapped[int] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(String(32), index=True)
    type: Mapped[str] = mapped_column(String(16))  # article | video | tip
    title_ar: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[str] = mapped_column(String(200))
    summary_ar: Mapped[str] = mapped_column(Text)
    summary_en: Mapped[str] = mapped_column(Text)
    body_ar: Mapped[str] = mapped_column(Text, default="")
    body_en: Mapped[str] = mapped_column(Text, default="")
    minutes: Mapped[int] = mapped_column(Integer, default=3)

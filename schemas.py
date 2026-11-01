from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Locale = Literal["ar", "en"]
Theme = Literal["light", "dark", "system"]
Mode = Literal["in_person", "video", "audio"]
Service = Literal["mental", "fitness", "sports_medicine", "nutrition", "education"]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None
    birth_date: date | None = None
    gender: Literal["female", "male"] | None = None
    locale: Locale = "ar"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PrefsIn(BaseModel):
    locale: Locale | None = None
    theme: Theme | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = None


class UnlockIn(BaseModel):
    password: str
    sections: list[str] = ["mental"]


class AppointmentIn(BaseModel):
    specialist_id: int
    starts_at: datetime
    mode: Mode
    reason: str | None = Field(default=None, max_length=1000)
    shared_sections: list[str] = []


class RescheduleIn(BaseModel):
    starts_at: datetime


class MeasurementIn(BaseModel):
    kind: Literal["weight", "sleep_hours", "mood", "energy", "steps", "resting_hr"]
    value: float
    recorded_at: datetime | None = None


class CheckinIn(BaseModel):
    mood: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    sleep_hours: float = Field(ge=0, le=24)


class GoalIn(BaseModel):
    domain: Literal["mental", "physical", "nutrition", "general"]
    title: str = Field(min_length=2, max_length=160)
    start_value: float
    target_value: float
    unit: str = ""
    target_date: date | None = None


class GoalProgressIn(BaseModel):
    current_value: float


class ShareIn(BaseModel):
    specialist_id: int
    sections: list[str] = Field(min_length=1)
    duration: Literal["session", "month", "until_revoked"] = "month"


class PlanLogIn(BaseModel):
    item_id: int
    day: date
    done: bool = True


class PlanChangeIn(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


class MessageIn(BaseModel):
    specialist_id: int
    body: str = Field(min_length=1, max_length=4000)


class AssistantIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    locale: Locale = "ar"
    history: list[dict] = []

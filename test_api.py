"""End-to-end API tests on a throwaway SQLite database with demo data."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "test_tawazun.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB.as_posix()}"
os.environ["SEED_DEMO_DATA"] = "true"
os.environ["LLM_TEST"] = "1"

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="module")
def client():
    if DB.exists():
        DB.unlink()
    from app.main import app
    with TestClient(app) as c:
        yield c
    DB.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def auth(client):
    r = client.post("/api/auth/login", json={"email": "demo@tawazun.app", "password": "Demo@1234"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_requires_auth(client):
    assert client.get("/api/card").status_code == 401


def test_register_and_prefs(client):
    r = client.post("/api/auth/register", json={"email": "new@x.com", "password": "Strong#Pass1", "full_name": "Test User"})
    assert r.status_code == 201
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.patch("/api/auth/me", json={"locale": "en", "theme": "dark"}, headers=h)
    assert r.json()["locale"] == "en" and r.json()["theme"] == "dark"
    assert client.post("/api/auth/register", json={"email": "new@x.com", "password": "Strong#Pass1", "full_name": "Dup"}).status_code == 409


def test_card_locks_mental_until_unlocked(client, auth):
    card = client.get("/api/card", headers=auth).json()
    mental = next(i for i in card["indicators"] if i["domain"] == "mental")
    assert mental.get("locked") is True
    assert all(r["domain"] != "mental" for r in card["recent_results"])
    assert client.get("/api/card/results?domain=mental", headers=auth).status_code == 423

    assert client.post("/api/card/unlock", json={"password": "wrong"}, headers=auth).status_code == 401
    tok = client.post("/api/card/unlock", json={"password": "Demo@1234"}, headers=auth).json()["unlock_token"]
    card = client.get("/api/card", headers={**auth, "X-Unlock-Token": tok}).json()
    mental = next(i for i in card["indicators"] if i["domain"] == "mental")
    assert mental["value"] == 6 and mental["trend"] == "improving"


def test_indicators_and_results(client, auth):
    card = client.get("/api/card", headers=auth).json()
    phys = next(i for i in card["indicators"] if i["domain"] == "physical")
    assert phys["value"] == 38 and phys["trend"] == "improving" and len(phys["spark"]) >= 2
    vit = next(r for r in client.get("/api/card/results", headers=auth).json() if r["name"]["en"] == "Vitamin D")
    assert vit["status"] == "low" and vit["previous"] == 16
    assert card["alerts"]["blood_type"] == "O+"


def test_booking_flow(client, auth):
    sps = client.get("/api/specialists?service=nutrition", headers=auth).json()
    assert sps and all(s["service"] == "nutrition" for s in sps)
    sp = sps[0]
    days = client.get(f"/api/specialists/{sp['id']}/availability?days=7", headers=auth).json()
    slot = next(s for d in days for s in d["slots"])
    mode = sp["modes"][0]
    r = client.post("/api/appointments", json={"specialist_id": sp["id"], "starts_at": slot, "mode": mode,
                                               "shared_sections": ["nutrition"]}, headers=auth)
    assert r.status_code == 201, r.text
    appt = r.json()
    # same slot can't be double-booked
    assert client.post("/api/appointments", json={"specialist_id": sp["id"], "starts_at": slot, "mode": mode}, headers=auth).status_code == 409
    assert any(a["id"] == appt["id"] for a in client.get("/api/appointments", headers=auth).json())
    assert client.post(f"/api/appointments/{appt['id']}/cancel", headers=auth).json()["status"] == "cancelled"


def test_plans_and_logging(client, auth):
    plans = client.get("/api/plans", headers=auth).json()
    assert {p["kind"] for p in plans} == {"training", "nutrition", "mental"}
    today = client.get("/api/plans/today", headers=auth).json()
    assert today["tasks"]
    t = today["tasks"][0]
    assert client.post("/api/plans/log", json={"item_id": t["id"], "day": today["date"], "done": True}, headers=auth).status_code == 200
    again = client.get("/api/plans/today", headers=auth).json()
    assert next(x for x in again["tasks"] if x["id"] == t["id"])["done"] is True
    detail = client.get(f"/api/plans/{t['plan_id']}", headers=auth).json()
    assert len(detail["weekly_adherence"]) == 6
    assert client.post(f"/api/plans/{t['plan_id']}/change-request", json={"message": "أصعب من اللازم"}, headers=auth).status_code == 201


def test_sharing_and_audit(client, auth):
    sp = client.get("/api/specialists?service=fitness", headers=auth).json()[0]
    g = client.post("/api/shares", json={"specialist_id": sp["id"], "sections": ["physical", "goals"], "duration": "session"}, headers=auth).json()
    assert g["active"]
    assert client.post("/api/shares", json={"specialist_id": sp["id"], "sections": ["bank"]}, headers=auth).status_code == 422
    assert client.post(f"/api/shares/{g['id']}/revoke", headers=auth).json()["active"] is False
    log = client.get("/api/shares/access-log", headers=auth).json()
    assert {"share", "revoke"} <= {e["action"] for e in log}


def test_checkin_goals_measurements(client, auth):
    assert client.post("/api/card/checkin", json={"mood": 4, "energy": 3, "sleep_hours": 7}, headers=auth).status_code == 201
    assert client.get("/api/card/checkin/today", headers=auth).json()["done"] is True
    client.post("/api/card/measurements", json={"kind": "weight", "value": 73.6}, headers=auth)
    g = next(g for g in client.get("/api/card/goals", headers=auth).json() if g["unit"] == "kg")
    assert g["current_value"] == 73.6 and 0 < g["progress"] < 1
    assert client.get("/api/card/series?kind=weight", headers=auth).json()[-1]["v"] == 73.6


def test_messages_encrypted_at_rest(client, auth):
    threads = client.get("/api/messages/threads", headers=auth).json()
    sid = threads[0]["specialist"]["id"]
    client.post("/api/messages", json={"specialist_id": sid, "body": "سؤال سري"}, headers=auth)
    assert client.get(f"/api/messages/{sid}", headers=auth).json()[-1]["body"] == "سؤال سري"
    from app.db import SessionLocal
    from app.models import Message
    with SessionLocal() as db:
        raw = db.query(Message).order_by(Message.id.desc()).first().body
    assert raw.startswith("enc:") and "سري" not in raw
    # no messaging with specialists the user never booked
    assert client.get("/api/messages/9999", headers=auth).status_code == 403


def test_timeline_content_notifications(client, auth):
    tl = client.get("/api/card/timeline", headers=auth).json()
    assert tl and all(e["domain"] != "mental" for e in tl)
    assert len(client.get("/api/content?service=nutrition", headers=auth).json()) >= 2
    n = client.get("/api/notifications", headers=auth).json()
    assert "smart" in n and n["items"]


def test_assistant_crisis_safety_and_provider_failure(client, auth):
    r = client.post("/api/assistant/chat", json={"message": "I want to end my life", "locale": "en"}, headers=auth).json()
    assert r["safety"] is True and "999" in r["reply"]
    # no local model running in tests → graceful 503, not a crash
    r = client.post("/api/assistant/chat", json={"message": "What is a healthy breakfast?", "locale": "en"}, headers=auth)
    assert r.status_code in (200, 503)


def test_llm_factory_switches_provider():
    from app.llm import build_provider
    assert build_provider("ollama").name == "ollama"
    assert build_provider("openai").name == "openai"
    assert build_provider("openai_compatible").name == "openai_compatible"
    with pytest.raises(ValueError):
        build_provider("nope")

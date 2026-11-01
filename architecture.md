# Architecture

```
┌──────────────── frontend (React + Vite) ────────────────┐
│ pages/  Home · Book · Appointments · Plans · Card · …   │
│ state.jsx  locale/RTL · theme · session · toasts        │
│ api/client.js  JWT + X-Unlock-Token                     │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS / JSON  (/api/*)
┌──────────────────────────┴──────────────────────────────┐
│ backend (FastAPI)                                       │
│  routers/  auth · specialists · appointments · card ·   │
│            plans · shares · messages · notifications ·  │
│            content · assistant                          │
│  deps.py   current user · unlock scope · audit          │
│  core/     config (YAML + .env) · logging · security    │
│  llm/      LLMProvider → Ollama | OpenAI | compatible   │
└──────────────┬────────────────────────────┬─────────────┘
               │ SQLAlchemy                 │ httpx
        SQLite (dev) / PostgreSQL     Ollama :11434 / OpenAI API
```

## Configuration
| Source | Holds | Selected by |
| --- | --- | --- |
| `config/config.yaml`, `config/config.prod.yaml` | project settings: booking hours, slot length, privacy rules, LLM provider + model + prompt, logging | `CONFIG_FILE` in the env file |
| `.env`, `.env.prod` | secrets, DB URL, provider URLs/keys, seed flag, `VITE_API_URL` | `APP_ENV` (`dev` default, `prod`) |

## Security & privacy
- **Auth:** bcrypt password hashes, short-lived JWT access tokens (60 min dev / 30 min prod). Web session lives in `sessionStorage`, so it ends with the browser.
- **Locked sections:** sections in `privacy.locked_sections` (default `mental`) are withheld from every card endpoint until the user re-confirms identity (`POST /card/unlock`), which returns a 5-minute scoped token.
- **Encryption at rest:** messages and mental-health session summaries use Fernet (`FIELD_ENCRYPTION_KEY`).
- **Consent sharing:** `ShareGrant` per specialist, per section, with expiry (one session / month / until revoked). Booking can attach a one-day grant.
- **Audit:** `AccessLog` records view / unlock / share / revoke; users see it under *Manage sharing*.
- **Headers:** `no-store` caching, `nosniff`, `DENY` framing, `no-referrer`. API docs disabled in prod.
- **Assistant safety:** crisis wording short-circuits to emergency guidance before any model call; the system prompt forbids diagnosis or plan changes.

## Smart behaviour
- Specialist list sorted by soonest free slot, then rating.
- Slots computed from `booking.*` config minus existing bookings; double-booking returns `409 slot_unavailable`.
- Indicators compare each headline result with the previous one; `lower_is_better` decides the trend direction.
- Plans: daily items, logs, weekly adherence; `suggest_review` when two consecutive weeks fall under `plans.low_adherence_threshold`.
- Notifications: stored events plus computed reminders (appointment within 24 h, missing daily check-in).

## Extending the AI layer
```python
class MyProvider(LLMProvider):
    name = "mine"
    async def chat(self, messages): ...
# register in llm/factory.py and add llm.providers.mine.model to config
```

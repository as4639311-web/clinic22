# Tawazun Clinic — project context

Integrated clinic app for booking and follow-up across five services: mental health, fitness, sports medicine, nutrition and health education. The **personal health card** is the core of the product. Arabic-first (RTL) with full English (LTR), light/dark mode, mobile-first.

## Stack
- **backend/** — Python 3.11+, FastAPI, SQLAlchemy 2 (SQLite in dev, PostgreSQL in prod), JWT auth, bcrypt, Fernet field encryption.
- **frontend/** — React 18 + Vite, React Router, lucide-react icons, plain CSS with logical properties (no CSS framework).

## Template conventions (keep these)
- `config/` at the root only: `config.yaml` (dev) and `config.prod.yaml` (prod) hold **project settings**.
- `.env` (dev) and `.env.prod` (prod) at the root hold **environment values**: secrets, URLs, DB. `APP_ENV=prod` switches both.
- `log/` at the root — rotating `app.log` (level/size from config).
- `docs/` — architecture, API, data model, design system.
- AI layer: `backend/app/llm/` — provider chosen by `llm.provider` in config (`ollama` | `openai` | `openai_compatible`), URLs/keys from env. Add a provider by subclassing `LLMProvider` and registering it in `factory.py`.

## Key rules
- Mental-health data is **locked by default** (`privacy.locked_sections`): the card hides it until `POST /api/card/unlock` returns a 5-minute unlock token sent as `X-Unlock-Token`.
- Mental session summaries and all messages are **encrypted at rest** (`enc:` prefix). Set `FIELD_ENCRYPTION_KEY` in production.
- Every card view/unlock/share/revoke is written to `access_logs` and shown to the user.
- The assistant checks for crisis wording **before** calling any model and returns the safety message (999 in the UAE) immediately.
- Bilingual content is stored as `*_ar` / `*_en` columns and returned as `{"ar": …, "en": …}`; the client picks by locale.
- Timestamps: appointments are naive clinic-local time; everything else is naive UTC and serialized with `Z` (`serial.iso_utc`).

## Commands
```bash
cd backend && pip install -r requirements.txt && python run.py   # API on :8000, docs at /docs (dev only)
cd backend && python -m pytest -q tests                             # 13 end-to-end tests
cd frontend && npm install && npm run dev                           # UI on :5173
```
Demo login: `demo@tawazun.app` / `Demo@1234` (seeded when `SEED_DEMO_DATA=true`).

## Layout
```
backend/app/
  core/ config.py, logging.py, security.py, clock.py
  llm/  base.py, providers.py, factory.py
  routers/ auth, specialists, appointments, card, plans, shares, messages, notifications, content, assistant
  models.py, schemas.py, serial.py, deps.py, seed.py, main.py
frontend/src/
  api/client.js, state.jsx, i18n/strings.js, components/ui.jsx, pages/*.jsx, styles/app.css
```

## Not built yet (next steps)
Specialist/admin portal, real video calls (e.g. WebRTC/Twilio), push notifications, payments/insurance, file upload for lab reports, biometric unlock on native mobile, FHIR export.

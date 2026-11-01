# API reference

Base: `/api`. All endpoints except `auth/register`, `auth/login` and `health` need `Authorization: Bearer <token>`. Errors return `{"detail": "<code>"}`; the client maps codes to Arabic/English messages. Interactive docs: `http://127.0.0.1:8000/docs` (dev only).

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Create account → `{access_token, user}` |
| POST | `/auth/login` | Sign in → `{access_token, user}` |
| GET / PATCH | `/auth/me` | Profile; update `locale`, `theme`, `full_name`, `phone` |
| GET | `/specialists?service=&gender=&language=&mode=` | Specialists with `next_slot`, soonest first |
| GET | `/specialists/{id}` | One specialist |
| GET | `/specialists/{id}/availability?start=&days=` | Free slots per day |
| GET | `/appointments?scope=upcoming\|past` | User's appointments |
| POST | `/appointments` | Book `{specialist_id, starts_at, mode, reason?, shared_sections[]}` |
| GET | `/appointments/{id}` | Detail (decrypted summary) |
| POST | `/appointments/{id}/cancel` | Cancel |
| POST | `/appointments/{id}/reschedule` | Move `{starts_at}` |
| GET | `/card` | Full card: profile, alerts, indicators, next appointment, recent results, goals, history, active shares |
| POST | `/card/unlock` | `{password, sections}` → `{unlock_token, expires_in}`; send as `X-Unlock-Token` |
| GET | `/card/results?domain=` | All results with previous value, trend, status (423 if locked) |
| GET | `/card/series?assessment=\|kind=&days=` | Time series for charts |
| POST | `/card/measurements` | Add weight / sleep / mood … (weight updates kg goals) |
| POST | `/card/checkin` · GET `/card/checkin/today` | 10-second daily check-in |
| GET / POST | `/card/goals` · PATCH `/card/goals/{id}` | Goals |
| GET | `/card/timeline?domain=` | Consultations, results, achievements |
| GET | `/plans` · `/plans/today` · `/plans/{id}` | Plans, today's tasks, detail with 6-week adherence |
| POST | `/plans/log` | Mark an item done `{item_id, day, done}` |
| POST | `/plans/{id}/change-request` | Ask the specialist to adjust |
| GET / POST | `/shares` · POST `/shares/{id}/revoke` | Consent sharing |
| GET | `/shares/access-log` | Who viewed or changed access, when |
| GET | `/messages/threads` · `/messages/{specialist_id}` · POST `/messages` | Encrypted messaging (only with booked specialists) |
| GET | `/notifications` · POST `/notifications/read-all` | Stored + smart reminders |
| GET | `/content?service=&type=&q=` · `/content/{id}` | Education library |
| POST | `/assistant/chat` | `{message, locale, history}` → `{reply, safety, provider}` (503 if model offline) |
| GET | `/assistant/status` | Active provider and model |

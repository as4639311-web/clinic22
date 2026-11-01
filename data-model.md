# Data model — the personal card

Each entity carries a sensitivity level that decides sharing and locking.

| Entity | Key fields | Sensitivity |
| --- | --- | --- |
| `User` | email, full_name, birth_date, gender, avatar, locale, theme, file_number | normal |
| `MedicalHistory` | blood_type, chronic_conditions, medications, allergies, surgeries, injuries, family_history (bilingual JSON lists) | high |
| `Assessment` | domain (mental/physical/nutrition/general), kind (scale/test/lab/body), name, value, unit, range, lower_is_better, taken_at, specialist, note | by domain — mental is locked |
| `Measurement` | kind (weight, sleep_hours, mood, energy, steps, resting_hr), value, source (manual/device), recorded_at | normal |
| `Goal` | domain, title, start/target/current value, unit, target_date, status | normal (mental goals locked) |
| `Appointment` | specialist, service, starts_at, mode, status, reason, summary, shared_sections | medium; mental summary encrypted |
| `Plan` → `PlanItem` → `PlanLog` | kind (training/nutrition/mental), version, weekday items, daily done logs | medium |
| `PlanChangeRequest` | plan, message | medium |
| `ShareGrant` | specialist, sections, starts_at, expires_at, revoked | — |
| `AccessLog` | actor, action, section, at | — |
| `Message` | specialist, sender, body (encrypted) | high |
| `Notification` | kind, bilingual title/body, read | normal |
| `Content` | service, type (article/video/tip), bilingual title/summary/body, minutes | public |

Card sections used for sharing: `profile, history, mental, physical, nutrition, goals, appointments, plans`.

FHIR mapping for later integration: User→Patient, Assessment/Measurement→Observation, Plan→CarePlan, Appointment→Appointment, ShareGrant→Consent.

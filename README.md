# توازن | Tawazun Clinic

تطبيق عيادة متكامل لحجز المواعيد والمتابعة في: الصحة النفسية، اللياقة البدنية، الطب الرياضي، التغذية، والتثقيف الصحي — والبطاقة الصحية الشخصية في قلبه.

An integrated clinic app for booking and follow-up across mental health, fitness, sports medicine, nutrition and health education, built around a personal health card.

## التشغيل السريع | Quick start

**المتطلبات:** Python 3.11+ و Node.js 18+

```bash
# 1) الخادم | API
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python run.py                   # http://127.0.0.1:8000  — API docs: /docs

# 2) الواجهة | Web app (terminal ثانٍ)
cd frontend
npm install
npm run dev                     # http://127.0.0.1:5173
```

ادخل بالحساب التجريبي: **demo@tawazun.app** / **Demo@1234** (أو زر «استخدم الحساب التجريبي»).

## المساعد الصحي (اختياري) | Health assistant
- **Ollama محلياً:** ثبّت Ollama ثم `ollama pull llama3.1:8b` — الإعداد الافتراضي في `config/config.yaml`.
- **OpenAI:** غيّر `llm.provider: "openai"` في `config/config.yaml` وضع المفتاح في `.env` → `OPENAI_API_KEY`.
- **أي خادم متوافق مع OpenAI** (LM Studio, vLLM): `llm.provider: "openai_compatible"` + `OPENAI_COMPAT_BASE_URL`.

## الإنتاج | Production
```bash
set APP_ENV=prod                 # macOS/Linux: export APP_ENV=prod
python backend/run.py            # يقرأ .env.prod و config/config.prod.yaml
cd frontend && npm run build:prod
```
املأ القيم في `.env.prod` (SECRET_KEY، FIELD_ENCRYPTION_KEY، DATABASE_URL، OPENAI_API_KEY) قبل التشغيل.

## الاختبارات | Tests
```bash
cd backend && python -m pytest -q tests
```

## الهيكل | Structure
| المسار | المحتوى |
| --- | --- |
| `config/` | إعدادات المشروع: `config.yaml` (تطوير) و `config.prod.yaml` (إنتاج) |
| `.env` / `.env.prod` | قيم البيئة: الأسرار، الروابط، قاعدة البيانات |
| `log/` | سجلات التشغيل `app.log` |
| `docs/` | المعمارية، الواجهات البرمجية، نموذج البيانات، نظام التصميم |
| `backend/` | FastAPI + SQLAlchemy + طبقة الذكاء الاصطناعي |
| `frontend/` | React + Vite، عربي/إنجليزي، ليلي/نهاري |
| `claude.md` | سياق المشروع للعمل مع Claude |

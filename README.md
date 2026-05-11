# Clinsights

## 1. Product Overview
Clinsight is an AI-powered clinical support platform that helps users understand their laboratory test results instantly. Users upload a laboratory report as an image or PDF, and Clinsight extracts the medical values, interprets them using AI, and explains the results in plain, human language.
The MVP focuses on one core problem: people receive laboratory results but cannot understand what they mean without waiting for a doctor. Clinsight reduces that waiting time by giving users immediate explanations, risk indicators, and guidance on what questions to ask a doctor next.

## 2. Key Features
- **Guest Upload**: Upload + full AI interpretation without an account. Prompted to sign up after 3 responses.
- **Authentication**: Email/password signup with OTP verification. Google OAuth. Password reset. Session persistence.
- **Lab Results Upload**: Camera capture + file upload (JPG, PNG, PDF). Validation, loading, and error states included.
- **OCR Extraction**: Extracts test names, values, reference ranges. Preview screen before AI runs.
- **AI Interpretation**: Plain-language explanation. Summary + suggested questions. Medical disclaimer on every screen.
- **Follow-Up Chat**: Context-aware chat tied to each upload. Persistent thread per session. Suggested prompt questions for new users.
- **History**: Authenticated users can view, reopen, and delete past interpretations.
- **Notifications & Settings**: Push notification when interpretation is ready. Notification preferences, profile editing, email/password update, account deletion.

## 3. Tech Stack
- **Backend**: Python FastAPI
- **Authentication**: OTP-based (email/phone), no passwords, Google OAuth
- **OCR**: Document/image text extraction
- **Database**: PostgreSQL

## 4. Inputs & Outputs
| Feature | User Input | System Output |
| :--- | :--- | :--- |
| **Upload** | Photo or file (JPG/PNG/PDF) | Validated file → OCR pipeline |
| **OCR** | Uploaded image / PDF | Test names, values, reference ranges extracted |
| **AI Interpretation** | Confirmed OCR values | Plain-language explanations, summary, follow-up questions |
| **Chat** | Free-text question, Suggested questions | Context-aware AI response using report data |
| **Signup** | Email + password or Google OAuthentication | Account created; OTP verification email sent |
| **Guest Migration**| Sign up after guest upload | Guest session linked to account; interpretation saved |

## 5. High-Level Logic & Behaviour
- **Upload**: Accepted: JPG, PNG, PDF. Unreadable/unsupported file → error state + reupload. OCR timeout at 15s → error + reupload.
- **AI Engine**: Classifies each value as Normal / Caution / Abnormal against reference. Disclaimer appended automatically. AI error → fallback message + retry.
- **Guest Flow**: Upload-to-interpretation without account. The session expires in 1hr. Sign-up prompt on: After 3 messages; chat history migration is automatic on signup.
- **Auth & Session**: OTP valid 15 mins, single-use. Password reset link expires in 1hr. Google OAuth via OAuth 2.0. Tokens stored securely on device.
- **Notifications**: Push sent on interpretation complete. Suppressed if the user is actively on the result screen. Users who opt out can still access results in-app.

## 6. Acceptance Criteria
- **Lab result uploaded in under 30 seconds**: ≤ 30s
- **OCR extracts values accurately**: 85%+
- **AI interpretation generated successfully**: 90%+
- **AI interpretation completes within 15 seconds**: < 15s
- **Chat produces context-aware responses**: Pass
- **Guest session migrates without data loss**: Pass
- **Authentication flows complete without errors**: Pass
- **Crash-free sessions across core flow**: 95%+
- **Medical disclaimer on every interpretation screen**: 100%
- **Users can view past interpretations**: Pass

## 7. Out of Scope
- Doctor/patient matching & telemedicine
- Doctor dashboard, onboarding, verification
- PDF export
- Long-term patient health tracking
- Multi-language support
- Hospital / lab system integrations
- AI learning loop & model retraining
- Admin analytics system

## Project structure

This is the **target layout for the full MVP**. Interns should follow this exactly — add files in the right domain folders rather than creating new top-level directories.

```text
clinsights-be/
├── app/
│   ├── main.py                            # FastAPI app, global exception handlers
│   ├── core/
│   │   ├── config.py                      # Settings loaded from .env (pydantic-settings)
│   │   └── security.py                    # JWT + password hashing utilities
│   ├── api/
│   │   ├── deps.py                        # Shared dependencies: DBSession, CurrentUser, GuestSession
│   │   └── v1/
│   │       ├── router.py                  # Aggregates all v1 domain routers
│   │       └── endpoints/
│   │           ├── auth.py                # /auth — signup, login, OTP verify, Google OAuth
│   │           ├── users.py               # /users — profile, settings, account deletion
│   │           ├── upload.py              # /upload — file upload (JPG, PNG, PDF)
│   │           ├── ocr.py                 # /ocr — trigger extraction, preview extracted values
│   │           ├── interpretation.py      # /interpretation — AI result + risk classification
│   │           ├── chat.py                # /chat — follow-up Q&A tied to an interpretation
│   │           ├── history.py             # /history — list, view, delete past interpretations
│   │           └── notifications.py       # /notifications — preferences, push settings
│   ├── db/
│   │   └── session.py                     # Async engine + session factory + get_session()
│   ├── models/
│   │   ├── __init__.py                    # Imports all models — required for Alembic discovery
│   │   ├── user.py                        # User ORM model
│   │   ├── otp.py                         # OTP codes
│   │   ├── lab_report.py                  # LabReport — file path, upload status, guest session link
│   │   ├── ocr_result.py                  # OCRResult — extracted test names, values, ranges
│   │   ├── interpretation.py              # Interpretation — AI output, risk level, disclaimer
│   │   ├── chat.py                        # ChatSession + ChatMessage — per-report chat threads
│   │   └── notification.py                # NotificationPreference — per-user push settings
│   ├── schemas/
│   │   ├── auth.py                        # Signup, Login, OTP request/response schemas
│   │   ├── user.py                        # User profile schemas
│   │   ├── upload.py                      # Upload response schemas
│   │   ├── ocr.py                         # OCR preview + confirm schemas
│   │   ├── interpretation.py              # AI interpretation response schemas
│   │   ├── chat.py                        # Chat message request/response schemas
│   │   ├── history.py                     # History list/detail schemas
│   │   └── notification.py                # Notification preference schemas
│   └── services/
│       ├── auth/                          # Modular auth services
│       │   ├── email.py                   # Auth-specific email dispatch
│       │   ├── otp.py                     # OTP generation + validation logic
│       │   ├── service.py                 # Core auth business logic
│       │   └── tokens.py                  # JWT lifecycle logic
│       ├── email.py                       # General transactional email client (Resend)
│       ├── oauth.py                       # Google OAuth integration
│       ├── upload.py                      # File validation, storage (local/S3), size checks
│       ├── ocr.py                         # OCR extraction pipeline (PDF/image → structured data)
│       ├── ai.py                          # AI interpretation engine — prompting, risk classification
│       ├── chat.py                        # Chat service — context injection, response generation
│       ├── guest.py                       # Guest session management + migration to user account
│       └── notification.py               # Push notification dispatch + preference management
├── alembic/
│   ├── env.py                             # Wired to app.models.Base.metadata + settings
│   └── versions/                          # Migration files — one per schema change
├── tests/                                 # Pytest suite
│   ├── smoke_test.py
│   ├── test_health.py
├── .env.example
├── alembic.ini
├── pyproject.toml
└── uv.lock
```

### Why this layout

- **`api/deps.py`** — all shared FastAPI dependencies live here. Routes import `DBSession`, `CurrentUser`, and `GuestSession` from one place.
- **`models` / `schemas` / `services` split** — DB shape, API shape, and business logic stay decoupled. They diverge faster than you'd think.
- **`db/session.py` separate from `models/`** — engine setup is infrastructure; models are domain.
- **One file per domain in `endpoints/`, `models/`, `schemas/`, `services/`** — makes it easy to find where any feature lives and keeps PRs focused.

---

## Getting started

### 1. Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A running Postgres instance (local, Docker, or Supabase)

### 2. Install

```bash
uv sync
```

### 3. Configure

```bash
cp .env.example .env
```

Fill in `.env` with your database credentials and secrets:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clinsights
JWT_SECRET=<generate: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
JWT_ALGORITHM=HS256
OTP_PEPPER=<generate: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
```

### 4. Database Setup

Ensure your local PostgreSQL database is created (`clinsights`) and the proper roles exist. Open your `psql` terminal and execute:

```sql
ALTER SCHEMA public OWNER TO postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT CREATE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON DATABASE clinsights TO postgres;
```

Then run migrations:

```bash
uv run alembic upgrade head
```

### 5. Start the dev server

```bash
uv run fastapi dev app/main.py
```

Or run via Uvicorn explicitly:

```bash
uv run uvicorn app.main:app --reload
```

- Root API → `http://127.0.0.1:8000`
- Swagger UI → `http://127.0.0.1:8000/docs`
- ReDoc → `http://127.0.0.1:8000/redoc`

---

## Migrations workflow

We use Alembic integrated with `uv` to manage database schema migrations.

### Typical cycle

```bash
# 1. Edit a model in app/models/
# 2. Generate a migration
uv run alembic revision --autogenerate -m "describe the change"
# 3. Review the generated file carefully before applying
# 4. Apply
uv run alembic upgrade head
```

### Important: add new models to `app/models/__init__.py`

Alembic discovers models by importing them. If a model file is not imported in `__init__.py`, Alembic won't see it.

```python
# app/models/__init__.py — every model must be listed here
from app.models.user import User
from app.models.otp import OTP
```

---

## Adding new code

### New endpoint
1. Add route handlers to the relevant file in `app/api/v1/endpoints/`
2. Import and register in `app/api/v1/router.py`

### New model
1. Create or extend a file in `app/models/`
2. Import the model in `app/models/__init__.py` so Alembic discovers it
3. Generate and apply a migration

### New schema
Add Pydantic request/response models to `app/schemas/`. Keep them separate from ORM models.

### New business logic
Add it to `app/services/`. Routes should stay thin: validate input → call service → return response.

---

## Contributing

1. Fork the repository and create your feature branch (`git checkout -b feature/your-feature`)
2. Install dependencies: `uv sync`
3. Run tests before committing: `uv run pytest`
4. Install pre-commit hook (`uv run pre-commit install`)
5. Commit your changes (`git commit -m 'Add feature'`)
6. Push to your branch (`git push origin feature/your-feature`)
7. Open a Pull Request

### Guidelines

- Follow existing code style and conventions
- Write clear, descriptive commit messages
- Include tests for new features
- Keep PRs focused and manageable in size
- Never commit secrets, keys, or credentials

# Signup, Login, and Email Verification (OTP)

This document describes the passwordless authentication flow added on the
`feature/signup-login-flow` branch. It covers the database changes, services,
HTTP endpoints, environment variables, and how to run everything locally.

## TL;DR for the frontend

The signup form sends `first_name`, `last_name`, and `email`. There are no
passwords. Authentication happens through 6-digit OTPs delivered by email.

| Step                | Method | Path                | Body                                                   |
| ------------------- | ------ | ------------------- | ------------------------------------------------------ |
| Sign up             | `POST` | `/api/v1/auth/signup`     | `{ first_name, last_name, email }`               |
| Verify (after signup or login) | `POST` | `/api/v1/auth/verify-otp` | `{ email, code, purpose }` where `purpose` is `email_verification` or `login` |
| Start login         | `POST` | `/api/v1/auth/login`      | `{ email }`                                       |
| Resend OTP          | `POST` | `/api/v1/auth/resend-otp` | `{ email, purpose }`                              |
| Get current user    | `GET`  | `/api/v1/auth/me`         | `Authorization: Bearer <jwt>`                     |

`/auth/verify-otp` returns `{ access_token, token_type, expires_in, user }`.
The frontend stores `access_token` and sends it as `Authorization: Bearer <token>`
on protected requests.

## Files added or changed

### Infrastructure

- `docker-compose.yml` — runs Postgres 16 (alpine) using vars from `.env`, with
  a named volume (`clinsights_postgres_data`) and a healthcheck.
- `.env.example` — documents every variable the app needs (Postgres, JWT, OTP, Resend).
- `.env` — local development defaults so `uv run fastapi dev` works out of the box.
  (Already gitignored.)
- `pyproject.toml` — added `pyjwt>=2.10.1` for signing JWT access tokens.

### Configuration

- `app/core/config.py` — added settings for JWT (`JWT_SECRET`, `JWT_ALGORITHM`,
  `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`), OTP (`OTP_LENGTH`, `OTP_EXPIRES_MINUTES`,
  `OTP_MAX_ATTEMPTS`, `OTP_PEPPER`), and Resend (`RESEND_API_KEY`,
  `RESEND_FROM_EMAIL`, `RESEND_FROM_NAME`).

### Models / DB

- `app/models/user.py` — split `name` into `first_name` and `last_name`,
  added a `full_name` convenience property, indexed `email`, and added the
  `otp_codes` relationship.
- `app/models/otp.py` — new `OtpCode` model with a `purpose` enum
  (`email_verification`, `login`), peppered SHA-256 `code_hash`, `attempts`,
  `expires_at`, `consumed_at`, `created_at`, and an `ON DELETE CASCADE` to `users`.
- `app/models/__init__.py` — registers the new model so Alembic picks it up.
- `alembic/versions/b9f2c1a47e21_add_otp_codes_and_split_user_name.py` — adds
  `otp_codes`, the `otppurpose` enum, and migrates `users.name` →
  `users.first_name` + `users.last_name` (data is preserved via `split_part`).

### Schemas

- `app/schemas/user.py` — uses `first_name`/`last_name` everywhere.
- `app/schemas/auth.py` — request/response shapes for signup, login,
  verify, resend, and the `TokenResponse` returned after authentication.
- `app/schemas/__init__.py` — re-exports the new schemas.

### Services

All auth services live under `app/services/auth/`:

- `tokens.py` — `create_access_token(user_id)` and `decode_access_token(token)`
  using HS256 and `JWT_SECRET`. Returns `(token, ttl_seconds)`.
- `otp.py` — generates cryptographically random N-digit codes, stores only a
  peppered SHA-256 hash, invalidates the previous active code per
  `(user, purpose)`, enforces expiry and `OTP_MAX_ATTEMPTS`, and burns the code
  after a successful verification or after the attempt limit is hit.
- `email.py` — sends the OTP email via Resend. If `RESEND_API_KEY` is empty
  (local dev), it logs the OTP to stdout via the `logger` instead of
  dispatching a real email. Includes both HTML and plain-text bodies.
- `service.py` — high-level orchestration (`signup_user`, `start_login`,
  `authenticate_otp`, `resend_otp`) that the API endpoints call into.

### API

- `app/api/deps.py` — adds `get_current_user` and a `CurrentUser` annotated
  alias that resolves the JWT from the `Authorization: Bearer …` header,
  decodes it, and loads the active `User` row.
- `app/api/v1/endpoints/auth.py` — five endpoints: `POST /auth/signup`,
  `POST /auth/login`, `POST /auth/verify-otp`, `POST /auth/resend-otp`,
  `GET /auth/me`.
- `app/api/v1/router.py` — wires the auth router into the v1 API.

## Flow walkthroughs

### Signup → email verification

1. Frontend submits `POST /api/v1/auth/signup` with `first_name`, `last_name`,
   `email`.
2. Backend creates an unverified `User` (or reuses the existing one if it was
   never verified — names are refreshed) and mints a 6-digit OTP with
   `purpose=email_verification`. The plaintext code is sent via Resend; only
   its SHA-256+pepper hash is persisted.
3. Frontend collects the code from the user and submits
   `POST /api/v1/auth/verify-otp` with `email`, `code`,
   `purpose: "email_verification"`.
4. Backend verifies the OTP (expiry, attempts, hash match), marks the user
   `is_email_verified = true`, sets `last_login_at`, and returns a JWT.

If the user already exists *and* is verified, signup returns `409 Conflict`.

### Login

1. `POST /api/v1/auth/login` with `email`.
2. Backend looks up the user. If missing → `404`. If inactive → `403`. If
   not yet email-verified → `403` with a message asking them to finish signup.
3. Otherwise a `purpose=login` OTP is dispatched to the user's email.
4. Frontend submits `POST /api/v1/auth/verify-otp` with `purpose: "login"`.
   On success the backend returns a fresh JWT.

### Resend

`POST /api/v1/auth/resend-otp` with `email` and `purpose`. Re-sending
invalidates the previous active code for the same `(user, purpose)` pair.

### Authenticated requests

Use the JWT returned by `/auth/verify-otp`:

```
Authorization: Bearer <access_token>
```

Endpoints that require auth take the `CurrentUser` dependency
(`from app.api.deps import CurrentUser`). `/auth/me` is the canonical example.

## Security notes

- **No passwords**, per the README's auth philosophy. The pre-existing
  `password_hash` and `google_id` columns are kept (nullable) for the
  upcoming Google OAuth branch but are not used by this flow.
- **Codes are never stored in plaintext.** They are hashed with SHA-256 using
  a server-side pepper (`OTP_PEPPER`). Verification uses
  `hmac.compare_digest`.
- **One live code per `(user, purpose)`.** Issuing a new code consumes any
  previous active code so a stolen older code is useless.
- **Rate limited per code.** After `OTP_MAX_ATTEMPTS` (default 5) wrong
  guesses on a single OTP, the code is burned and a new one must be requested.
  (Per-IP rate limiting at the edge is still recommended — out of scope here.)
- **Short expiry.** Default 10 minutes (`OTP_EXPIRES_MINUTES`).
- **JWT secret comes from env**, never committed. `OTP_PEPPER` and
  `JWT_SECRET` should both be rotated for production and generated as
  `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

## Environment variables

See `.env.example` for the canonical list. The new groups are:

```
# JWT
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60

# OTP
OTP_LENGTH=6
OTP_EXPIRES_MINUTES=10
OTP_MAX_ATTEMPTS=5
OTP_PEPPER=...

# Resend
RESEND_API_KEY=        # leave empty in dev to log OTPs to stdout
RESEND_FROM_EMAIL=onboarding@resend.dev
RESEND_FROM_NAME=Clinsights
```

## Running locally

```bash
# 1. Start Postgres
docker compose up -d postgres

# 2. Install deps (adds pyjwt)
uv sync

# 3. Apply migrations (splits users.name and creates otp_codes)
uv run alembic upgrade head

# 4. Run the API
uv run fastapi dev app/main.py
```

If `RESEND_API_KEY` is unset, OTPs are logged to your terminal so you can
test signup/login without an email provider.

## Quick smoke test (curl)

```bash
# Signup -> OTP is logged in your dev console (or sent via Resend).
curl -sX POST http://localhost:8000/api/v1/auth/signup \
	-H 'Content-Type: application/json' \
	-d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com"}'

# Verify the emailed code -> returns a JWT.
curl -sX POST http://localhost:8000/api/v1/auth/verify-otp \
	-H 'Content-Type: application/json' \
	-d '{"email":"ada@example.com","code":"123456","purpose":"email_verification"}'

# Subsequent login.
curl -sX POST http://localhost:8000/api/v1/auth/login \
	-H 'Content-Type: application/json' \
	-d '{"email":"ada@example.com"}'

curl -sX POST http://localhost:8000/api/v1/auth/verify-otp \
	-H 'Content-Type: application/json' \
	-d '{"email":"ada@example.com","code":"654321","purpose":"login"}'

# Authenticated call.
curl -s http://localhost:8000/api/v1/auth/me \
	-H "Authorization: Bearer $TOKEN"
```

## Open follow-ups

- Add per-IP / per-email rate limiting at the edge (e.g. `slowapi`) to
  complement the per-OTP attempt limit.
- Add refresh tokens if longer sessions are required.
- Wire Google OAuth in a follow-up branch using the existing `google_id`
  column on `users`.
- Tests: add `tests/test_auth.py` covering happy-path signup→verify→login,
  expiry, max-attempt lockout, and JWT auth on `/auth/me`.

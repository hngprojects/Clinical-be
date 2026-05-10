# Clinsights

AI-powered laboratory result interpretation and verified doctor second opinions for Nigerians.

## Core Features

- **Lab Upload & Parsing**: Upload PDF/image lab results; OCR extracts structured values
- **AI Interpretation**: Plain-language summaries, risk classification (Low/Moderate/High), and suggested next steps
- **Doctor Second Opinion**: Pay ₦2,500 for a verified doctor review with structured matching
- **AI Chat**: Contextual follow-up questions per lab report
- **72-Hour Shared Chat**: Post-review messaging window between patient and doctor
- **Passive Learning Loop**: Doctor corrections stored to improve future AI interpretations

## Tech Stack

- **Backend**: Python FastAPI
- **Authentication**: OTP-based (email/phone), no passwords
- **Payments**: Paystack
- **OCR**: Document/image text extraction

## User Roles

- **Patients**: Upload labs, receive AI interpretation, request doctor reviews
- **Doctors**: Verified medical professionals providing second opinions
- **Super Admin**: Credential verification, case monitoring, dispute management

## Project structure

This section shows the main folders and files in the repository so you can
find API routes, configuration, migrations, and tests quickly.

```text
.
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Database Setup

To set up your database locally, make sure you have PostgreSQL running. Use the default credentials found in your `.env.example` file to configure your local environment.

1. **Configure PostgreSQL Roles and Permissions**:
   Connect to your database (e.g., using `psql`) and execute the following commands to ensure proper schema ownership and privileges:

   ```sql
   ALTER SCHEMA public OWNER TO postgres;

   GRANT ALL ON SCHEMA public TO postgres;

   GRANT CREATE ON SCHEMA public TO postgres;

   GRANT USAGE ON SCHEMA public TO postgres;

   GRANT ALL PRIVILEGES ON DATABASE clinsights TO postgres;
   ```

2. **Database Migrations (Alembic)**:
   We use Alembic integrated with `uv` to manage database schema migrations.

   - **Run existing migrations** to update your database to the latest version:
     ```bash
     uv run alembic upgrade head
     ```
   
   - **Create a new migration revision** after making changes to your SQLAlchemy models:
     ```bash
     uv run alembic revision --autogenerate -m "your_migration_message"
     ```

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

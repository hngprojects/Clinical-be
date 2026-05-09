# Contributing to Clinical-be

Thank you for contributing! This document outlines the standards and processes we follow to maintain a clean, reliable codebase.

## Table of Contents

- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
- [Getting Started](#getting-started)
- [Branch Naming Convention](#branch-naming-convention)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)
- [Code of Conduct](#code-of-conduct)
- [License](#license)

---

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on [GitHub Issues](https://github.com/hngprojects/Clinical-be/issues) and include:

- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant logs or error messages
- Your environment (OS, Python version)

### Suggesting Features

If you have an idea for a new feature, please open an issue on [GitHub Issues](https://github.com/hngprojects/Clinical-be/issues) and describe:

- What problem the feature solves
- How it should work
- Any alternatives you considered

---

## Getting Started

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
4. Run the development server:
   ```bash
   uv run fastapi dev app/main.py
   ```
5. Run tests:
   ```bash
   uv run pytest
   ```

---

## Branch Naming Convention

All branches must follow this format:

```
<type>/<short-description>
```

| Type       | Purpose                          | Example                          |
|------------|----------------------------------|----------------------------------|
| `feat`     | New feature                      | `feat/user-authentication`       |
| `fix`      | Bug fix                          | `fix/token-expiry-handling`      |
| `refactor` | Code refactoring                 | `refactor/simplify-db-session`   |
| `docs`     | Documentation only               | `docs/update-api-readme`         |
| `test`     | Adding or updating tests         | `test/medical-case-coverage`     |
| `chore`    | Maintenance tasks                | `chore/upgrade-sqlalchemy`       |
| `hotfix`   | Urgent production fix            | `hotfix/crash-on-null-user`      |

**Rules:**
- Use lowercase and hyphens (no underscores or spaces)
- Keep descriptions concise (2-4 words)
- Never commit directly to `main`

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

| Type       | Description                              | Example                                      |
|------------|------------------------------------------|----------------------------------------------|
| `feat`     | A new feature for the user               | `feat(cases): add create medical case endpoint`|
| `fix`      | A bug fix for the user                   | `fix(auth): resolve token expiration issue`  |
| `docs`     | Documentation only changes               | `docs(readme): add setup instructions`       |
| `style`    | Changes that do not affect code meaning (formatting, whitespace) | `style(api): fix indentation` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor(utils): extract date formatting` |
| `perf`     | A code change that improves performance  | `perf(queries): add index for case lookup`   |
| `test`     | Adding missing tests or correcting existing tests | `test(health): add db failure case` |
| `build`    | Changes to build system or external dependencies | `build(deps): upgrade sqlalchemy to 2.1` |
| `ci`       | Changes to CI configuration and scripts  | `ci(github): add lint workflow`              |
| `chore`    | Other changes that don't modify src or test files | `chore: update .gitignore`            |
| `revert`   | Reverts a previous commit                | `revert: revert feat(cases) commit abc123`   |

### Rules

#### Subject (Required)
- Use imperative mood: "add" not "added" or "adds"
- Keep under 50 characters (hard limit: 72)
- Start with lowercase
- No period at the end
- Use present tense

#### Scope (Optional)
- Specifies the part of the codebase affected
- Use parentheses: `(auth)`, `(cases)`, `(db)`, `(api)`

#### Body (Optional)
- Separate from subject with a blank line
- Explain *what* and *why*, not *how*
- Wrap at 72 characters
- Use imperative mood

#### Footer (Optional)
- **Breaking changes**: `BREAKING CHANGE: <description>`
- **Issue references**: `Closes #123`, `Fixes #456`, `Relates to #789`
- **Co-authors**: `Co-authored-by: Name <email>`

### Examples

**Simple commit:**
```
feat(cases): add endpoint to create a medical case
```

**Commit with body:**
```
fix(auth): handle expired refresh tokens gracefully

The previous implementation did not check token expiry before
attempting to refresh, causing a 500 error for users with
expired sessions.

Closes #42
```

**Breaking change:**
```
feat(api): change medical case response format to include symptoms

BREAKING CHANGE: the medical case response object now nests symptom
data under a "symptoms" key instead of a flat "issues" array.
```

**Multiple issues:**
```
fix(notifications): resolve duplicate email sending

Duplicate emails were sent when a medical case was updated due to
the event handler firing twice.

Fixes #78
Relates to #65
```

### ❌ Bad Commit Messages

```
# Vague
fix: bug fix

# Multiple changes in one commit
feat: add login, fix header, update docs

# Wrong tense
feat: added new feature

# Missing context
refactor: change code
```

---

## Pull Request Process

1. Create a branch following the [naming convention](#branch-naming-convention)
2. Make your changes with [proper commits](#commit-message-convention)
3. Ensure all tests pass locally:
   ```bash
   uv run pytest
   ```
4. Push your branch and open a PR against `main`
5. Fill in the PR template completely — **incomplete PRs will not be reviewed**

### PR Requirements

Every pull request **must** include:

| Requirement | Details |
|-------------|---------|
| **Tests** | All new/modified functionality must have meaningful test cases |
| **Proof of work** | Screenshots of UI changes OR JSON responses from API endpoints |
| **Passing CI** | All existing and new tests must pass |
| **Description** | Clear explanation of what changed and why |

---

## Testing Requirements

All PRs must include test cases. Tests must be **meaningful** — they should verify behavior, not just existence.

### What Makes a Good Test

A meaningful test:
- Tests a specific behavior or business rule
- Has a descriptive name that explains what it verifies
- Covers both success and failure paths
- Is independent and can run in isolation

### Example: Testing an Endpoint

```python
# tests/test_medical_cases.py
import pytest
from httpx import AsyncClient


async def test_create_case_returns_201_with_valid_data(client: AsyncClient):
    """Creating a medical case with valid data should return 201 and the case object."""
    payload = {
        "guest_session_id": "session-123",
        "status": "pending",
    }

    response = await client.post("/api/v1/medical-cases", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["guest_session_id"] == "session-123"
    assert data["status"] == "pending"
    assert "id" in data


async def test_create_case_returns_422_without_required_fields(client: AsyncClient):
    """Creating a medical case without required fields should return 422 validation error."""
    payload = {}

    response = await client.post("/api/v1/medical-cases", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("guest_session_id" in e["loc"] or "user_id" in e["loc"] for e in errors)


async def test_list_cases_returns_empty_list_when_none_exist(client: AsyncClient):
    """Listing medical cases when none exist should return 200 with an empty list."""
    response = await client.get("/api/v1/medical-cases")

    assert response.status_code == 200
    assert response.json() == []
```

### Test Naming Convention

```
test_<action>_<expected_outcome>_<condition>
```

Examples:
- `test_create_user_returns_201_with_valid_email`
- `test_login_returns_401_with_wrong_password`
- `test_get_case_returns_404_when_not_found`

---

## Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Use `async/await` for all I/O operations
- Keep functions focused — one responsibility per function
- Place business logic in `app/services/`, not in endpoint handlers

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). By participating, you are expected to uphold this code.

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Questions?

If anything is unclear, open an issue or reach out to the maintainers.

# Backend tests

Pytest-based unit / integration tests for the FastAPI app.

## Running

```bash
# From the repo root, with the project venv active
pip install -r requirements.txt
pytest

# Or a single file
pytest tests/test_support_style.py -v
```

## How the harness works

- **DB**: SQLite in-memory with `StaticPool` so every connection sees the
  same database. The `test_engine` fixture monkey-patches
  `app.db.session.engine` and `SessionLocal` so the FastAPI lifespan
  startup and the tests both write to the test DB.
- **Sessions**: one `db_session` per test, with full row truncation at
  teardown so tests are independent.
- **Auth**: the `auth_headers(user)` fixture mints a real JWT against the
  test `JWT_SECRET_KEY`. For MFA-gated endpoints pass `mfa_verified=True`.
- **AI**: use `mock_ai_service` to swap the OpenAI/Anthropic clients for a
  recording mock — no real provider calls happen in tests.

## Adding a test

1. Drop a file in `tests/` named `test_*.py`.
2. Use the fixtures in `conftest.py` — they cover most setup.
3. If your endpoint touches the support-style catalogue, include the
   `synced_support_styles` fixture so the version cache is populated.

## Limitations

- SQLite isn't MySQL. Features like `INSERT ... ON DUPLICATE KEY UPDATE`,
  `JSON_EXTRACT` semantics, or InnoDB-specific behaviour won't be
  exercised here. For those, write an integration test that talks to a
  real MySQL container.
- The KMS startup check is bypassed in `test` env (config logs a warning
  rather than refusing to boot). Encryption tests should use the dev
  keyring path, not real KMS.

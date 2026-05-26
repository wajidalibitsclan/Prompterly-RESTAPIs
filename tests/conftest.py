"""
Shared test fixtures.

Strategy:
  * Spin up an in-process SQLite DB for the whole test session — fast,
    no MySQL needed.
  * Monkey-patch `app.db.session.engine` / `SessionLocal` so the app's
    lifespan startup (which calls `init_db()` and the support-style
    sync) writes to the SAME database the tests read from. Using
    `StaticPool` keeps the in-memory DB shared across connections.
  * Override the `get_db` FastAPI dependency so handlers see the test
    session.
  * Replace `ai_service` with a recording mock so we can assert prompt
    assembly without making real OpenAI / Anthropic calls.

Order-of-import matters: env vars MUST be set before `app.core.config`
loads (Pydantic-settings raises on missing required vars), and the
session module MUST be patched before any test imports `app.main`.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ---------------------------------------------------------------------------
# Required env vars BEFORE app.core.config is imported.
# ---------------------------------------------------------------------------
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-do-not-use-in-prod")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("ENCRYPTION_KEY", "0" * 64)
os.environ.setdefault("AI_DATA_OPT_OUT", "True")
os.environ.setdefault("REDIS_URL", "memory://")


@pytest.fixture(scope="session")
def test_engine():
    """One SQLite in-memory engine shared across the test session.

    StaticPool means every checkout returns the same underlying SQLite
    connection, so the in-memory DB is shared across the app, the test
    session, and any lifespan startup hooks.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Patch the production engine + SessionLocal to point at the test DB
    # BEFORE the app's modules import them. Done by directly mutating
    # `app.db.session` — every other module reads via attribute access.
    import app.db.session as session_mod
    session_mod.engine = engine
    session_mod.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine,
    )

    # Register models with Base.metadata, then create the schema.
    import app.db.models  # noqa: F401
    from app.db.session import Base
    Base.metadata.create_all(bind=engine)

    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    """One session per test, with full row cleanup at teardown."""
    from app.db.session import SessionLocal, Base
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Truncate every table so tests don't leak rows into each other.
        with test_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())


@pytest.fixture()
def client(db_session):
    """A FastAPI TestClient with `get_db` overridden to use our session."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def make_user(db_session):
    """Factory that creates a User row. Override defaults with kwargs."""
    from app.db.models.user import User, UserRole
    from app.core.security import hash_password
    from app.core.timezone import now_naive

    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        defaults = dict(
            email=f"user{counter['n']}@test.example",
            password_hash=hash_password("test-password-1234"),
            name=f"Test User {counter['n']}",
            role=UserRole.MEMBER,
            email_verified_at=now_naive(),
        )
        defaults.update(overrides)
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers():
    """Factory producing `{Authorization: Bearer ...}` headers for a User."""
    from app.core.security import create_access_token

    def _headers(user, mfa_verified: bool = False):
        claims = {"sub": str(user.id)}
        if mfa_verified:
            claims["mfa_verified"] = True
        token = create_access_token(data=claims)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture()
def synced_support_styles(db_session):
    """Ensure the support-style catalogue is mirrored to the test DB.

    Tests that touch chat threads or the support-style API need the
    `support_styles` / `support_style_versions` rows to exist. This
    runs the same sync that prod uses on startup.
    """
    from app.core.support_style import sync_support_style_versions_with_db
    sync_support_style_versions_with_db(db_session)
    return None


@pytest.fixture()
def mock_ai_service(monkeypatch):
    """Replace the singleton `ai_service` with a recording mock."""
    fake = MagicMock()
    fake.generate_chat_response = AsyncMock(
        return_value=("ok", {"model": "mock", "usage": {}}),
    )

    async def _fake_stream(*args, **kwargs):
        for chunk in ["ok"]:
            yield chunk

    fake.generate_chat_response_stream = _fake_stream
    fake.create_embedding = AsyncMock(return_value=[0.0] * 8)
    fake.create_embeddings_batch = AsyncMock(return_value=[[0.0] * 8])

    monkeypatch.setattr("app.services.chat_service.ai_service", fake, raising=True)
    return fake

"""Shared pytest fixtures.

Endpoint tests run against a separate PostgreSQL test database so the real
data is never touched. Set it before running:

    PowerShell:  $env:TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/helpdesk_test"
    bash:        export TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/helpdesk_test

Create the empty DB once:  createdb -U postgres helpdesk_test
Tables are built from database/schema.sql, so CHECK constraints match production.
Each test runs inside a transaction that is rolled back afterwards.

If TEST_DATABASE_URL is not set, or the backend app is not built yet, the
endpoint tests are skipped; the pure AI unit tests in test_ai.py still run.
"""
import os
import sys
from pathlib import Path

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCHEMA_SQL = BACKEND_DIR.parent / "database" / "schema.sql"
sys.path.insert(0, str(BACKEND_DIR))


# ---------------------------------------------------------------- database
@pytest.fixture(scope="session")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set - skipping database tests")
    from sqlalchemy import create_engine

    eng = create_engine(url)
    with eng.begin() as conn:
        conn.exec_driver_sql(SCHEMA_SQL.read_text(encoding="utf-8"))
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine):
    from sqlalchemy.orm import Session

    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def app(db_session):
    try:
        from app.db.session import get_db
        from app.main import app as fastapi_app
    except ImportError as e:
        pytest.skip(f"Backend app not ready yet ({e})")

    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture
def requester(db_session):
    from app.db.models import Requester

    r = Requester(display_name="Test User", contact="test.user@example.com", department="Finance")
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


@pytest.fixture
def ticket(db_session, requester):
    from app.db.models import Ticket

    t = Ticket(requester_id=requester.id, title="Keyboard keys sticking",
               description="A few keys stick sometimes. I can still type.")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


# ---------------------------------------------------------------- fake Ollama
def ollama_reply(content: str) -> httpx.Response:
    """Shape of a non-streaming Ollama /api/chat response."""
    return httpx.Response(200, json={"model": "qwen2.5:3b", "message": {"role": "assistant",
                                                                        "content": content},
                                     "done": True})


GOOD_JSON = ('{"category": "Hardware", "priority": "Low", '
             '"reason": "Single keyboard, user can still type.", '
             '"steps": ["Clean the keys", "Try another USB port", "Swap the keyboard"]}')


def make_client(handler, **kw):
    from app.services.ai.ollama_client import OllamaClient

    return OllamaClient(base_url="http://ollama.test", model="qwen2.5:3b", timeout=5,
                        transport=httpx.MockTransport(handler), **kw)


@pytest.fixture
def use_ai(app):
    """use_ai(handler) - make the API use a fake Ollama with this handler."""
    from app.services.ai.ollama_client import get_ollama_client

    def _install(handler):
        app.dependency_overrides[get_ollama_client] = lambda: make_client(handler)

    return _install

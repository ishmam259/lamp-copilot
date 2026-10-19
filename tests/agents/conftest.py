"""Chat tests: in-memory SQLite with the golden-number pharmacy, and the chat forced into
replay mode with an empty recordings folder, so no test ever calls OpenAI."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents import chat, llm
from app.db.seed import load_seed
from app.db.session import get_db
from app.main import app

_url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
engine = (create_engine(_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
          if _url.startswith("sqlite") else create_engine(_url))
TestSession = sessionmaker(bind=engine, expire_on_commit=False)
OWNER_PIN = "2468"  # the demo PIN (contracts/plan_v3.md); only its hash is in the seed


def _get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def replay_only(monkeypatch, tmp_path):
    monkeypatch.setattr(chat.settings, "llm_mode", "replay")
    monkeypatch.setattr(chat.settings, "openai_api_key", "")
    monkeypatch.setattr(chat, "REPLAY_DIR", tmp_path / "replay")
    monkeypatch.setattr(chat, "OFFLINE_SCRIPT", True)
    monkeypatch.setattr(llm, "SPEND_LOG", tmp_path / "spend.log")


@pytest.fixture
def client():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db
    with TestSession() as s:
        load_seed(s, with_demo_captures=True)
    c = TestClient(app)
    # Sign in like the app does: the owner PIN sets the session cookie.
    assert c.post("/api/v1/pharmacies/green-life/session", json={"pin": OWNER_PIN}).status_code == 200
    yield c
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous


@pytest.fixture
def db():
    with TestSession() as s:
        yield s

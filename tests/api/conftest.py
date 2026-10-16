"""In-memory SQLite database with the seed pharmacy, for API tests."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import load_seed
from app.db.session import get_db
from app.main import app

# SQLite in memory by default; set TEST_DATABASE_URL to run against PostgreSQL, e.g.
# postgresql+psycopg://lamp:lamp@localhost:5432/lamp_test
_url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
engine = (create_engine(_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
          if _url.startswith("sqlite") else create_engine(_url))
TestSession = sessionmaker(bind=engine, expire_on_commit=False)


def _get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_db


@pytest.fixture
def client():
    with TestSession() as s:
        load_seed(s, with_demo_captures=True)
    return TestClient(app)

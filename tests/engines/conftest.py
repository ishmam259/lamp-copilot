"""In-memory SQLite database with the seed pharmacy, for engine tests."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import load_seed

# SQLite in memory by default; set TEST_DATABASE_URL to run against PostgreSQL, e.g.
# postgresql+psycopg://lamp:lamp@localhost:5432/lamp_test
_url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
engine = (create_engine(_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
          if _url.startswith("sqlite") else create_engine(_url))
TestSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def db():
    """Seed plus the three demo captures: the state the golden numbers describe."""
    with TestSession() as s:
        load_seed(s, with_demo_captures=True)
        yield s


@pytest.fixture
def seed_only_db():
    with TestSession() as s:
        load_seed(s)
        yield s

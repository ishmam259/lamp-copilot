"""In-memory SQLite database with the seed pharmacy, for engine tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import load_seed

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

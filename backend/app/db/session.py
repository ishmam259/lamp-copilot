"""Engine and session factory. DATABASE_URL may be postgresql://... or sqlite:///..."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _url(raw: str) -> str:
    # Use the psycopg 3 driver for plain postgresql:// URLs.
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


engine = create_engine(_url(settings.database_url), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

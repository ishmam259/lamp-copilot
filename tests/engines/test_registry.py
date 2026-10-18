"""Duplicate-financing registry: commitments and the lock race."""

import os
import tempfile
import threading
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import models as m
from app.config import settings
from app.engines import registry


def test_commitment_is_stable_and_keyed(monkeypatch):
    a = registry.commitment(1, "A-1", "green-life", 60000, date(2026, 10, 26))
    assert a == registry.commitment(1, "A-1", "green-life", 60000.0, date(2026, 10, 26))
    assert len(a) == 64 and a != registry.commitment(1, "A-1", "green-life", 60000.01, date(2026, 10, 26))
    monkeypatch.setattr(settings, "registry_key", "other")
    assert a != registry.commitment(1, "A-1", "green-life", 60000, date(2026, 10, 26))


def test_lock_once(db):
    assert registry.try_lock(db, "c1", "APP-1") is True
    assert registry.try_lock(db, "c1", "APP-2") is False
    assert registry.try_lock(db, "c2", "APP-2") is True


def test_race_exactly_one_wins():
    """12 threads, each with its own connection, lock the same commitment at once."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url or url.startswith("sqlite"):
        url = f"sqlite:///{tempfile.mkdtemp()}/race.db"
    pg = url.startswith("postgresql")
    engine = create_engine(url, pool_size=20) if pg else create_engine(url, connect_args={"timeout": 30})
    m.RegistryLock.__table__.drop(engine, checkfirst=True)
    m.RegistryLock.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    start, wins, errors = threading.Barrier(12), [], []

    def worker(i):
        try:
            with Session() as s:
                start.wait()
                if registry.try_lock(s, "same-invoice", f"APP-{i}"):
                    wins.append(i)
                s.commit()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    with Session() as s:
        rows = s.query(m.RegistryLock).all()
    m.RegistryLock.__table__.drop(engine)
    engine.dispose()
    assert errors == [] and len(wins) == 1 and len(rows) == 1, (wins, errors)

"""Duplicate-financing registry.

Each financed receivable gets a commitment: a keyed hash that reveals nothing
about the invoice but is identical for the same invoice. A commitment can be
locked once; a second lender (or a second application) for the same invoice is
refused with reason `duplicate_financing`.
"""

import hashlib
import hmac
from datetime import date, datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.config import registry_secret
from app.db import models as m


def commitment(supplier_id: int, invoice_no: str, pharmacy_id: str, total: float, invoice_date: date) -> str:
    """hex HMAC-SHA256(REGISTRY_KEY, "{supplier_id}|{invoice_no}|{pharmacy_id}|{total:.2f}|{invoice_date}")."""
    msg = f"{supplier_id}|{invoice_no}|{pharmacy_id}|{total:.2f}|{invoice_date.isoformat()}"
    return hmac.new(registry_secret().encode(), msg.encode(), hashlib.sha256).hexdigest()


def try_lock(db: Session, value: str, application_id: str) -> bool:
    """INSERT ... ON CONFLICT (commitment) DO NOTHING RETURNING id.

    Returns True if this call took the lock, False if the commitment was already
    locked. Atomic in the database, so two concurrent callers cannot both win.
    """
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    stmt = (insert(m.RegistryLock)
            .values(commitment=value, application_id=application_id, created_at=datetime.now(timezone.utc))
            .on_conflict_do_nothing(index_elements=["commitment"])
            .returning(m.RegistryLock.id))
    return db.execute(stmt).scalar() is not None

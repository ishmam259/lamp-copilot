"""Owner sessions, the owner PIN and lender keys (win plan CORE-13).

- The owner unlocks with a PIN. Only its scrypt hash is stored, in pharmacy settings
  (`owner_pin`, "scrypt$<salt>$<hex>"). A correct PIN issues a random session token,
  stored in `owner_session` and sent to the browser as an HttpOnly cookie.
- Loan approvals re-ask the same PIN. That is re-authentication at the point of
  approval, not a second factor.
- Lenders call their own endpoints with a key; only its sha256 is stored on the lender.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m

SESSION_COOKIE = "lamp_session"
SESSION_HOURS = 12
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


def hash_pin(pin: str, salt: str) -> str:
    """"scrypt$<salt>$<hex digest>" for the pharmacy settings."""
    digest = hashlib.scrypt(pin.encode(), salt=salt.encode(), **_SCRYPT).hex()
    return f"scrypt${salt}${digest}"


def hash_key(key: str) -> str:
    """sha256 hex of a lender key (keys are long random strings, so no salt is needed)."""
    return hashlib.sha256(key.encode()).hexdigest()


def pin_ok(ph: m.Pharmacy, pin: str | None) -> bool:
    """Constant-time check of a PIN against the stored scrypt hash."""
    stored = (ph.settings or {}).get("owner_pin")
    if not pin or not stored or stored.count("$") != 2:
        return False
    _, salt, _ = stored.split("$")
    return hmac.compare_digest(hash_pin(pin, salt), stored)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_session(db: Session, pid: str) -> m.OwnerSession:
    """A new owner session for this pharmacy, valid for SESSION_HOURS."""
    now = _now()
    row = m.OwnerSession(token=secrets.token_urlsafe(32), pharmacy_id=pid, created_at=now,
                         expires_at=now + timedelta(hours=SESSION_HOURS))
    db.add(row)
    db.flush()
    return row


def session_for(db: Session, token: str | None) -> m.OwnerSession | None:
    """The live session for this cookie value, or None (missing, unknown or expired)."""
    if not token:
        return None
    row = db.get(m.OwnerSession, token)
    if row is None or row.expires_at <= _now():
        return None
    return row


def lender_for_key(db: Session, key: str | None) -> m.Lender | None:
    """The lender whose key this is, or None."""
    if not key:
        return None
    return db.scalar(select(m.Lender).where(m.Lender.api_key_sha256 == hash_key(key)))

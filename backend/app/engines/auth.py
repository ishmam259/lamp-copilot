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
# Wrong-PIN lockout: after MAX_PIN_FAILURES wrong tries in a row, PIN checks are refused for
# LOCKOUT_MINUTES (a 4-digit PIN otherwise falls to 10,000 guesses).
MAX_PIN_FAILURES = 5
LOCKOUT_MINUTES = 15
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


def locked_until(ph: m.Pharmacy) -> datetime | None:
    """When the wrong-PIN lockout ends, or None if PIN checks are open."""
    until = (ph.settings or {}).get("pin_locked_until")
    if until and datetime.fromisoformat(until) > _now():
        return datetime.fromisoformat(until)
    return None


def check_pin(db: Session, ph: m.Pharmacy, pin: str | None) -> bool:
    """pin_ok with the lockout: counts wrong tries, locks after MAX_PIN_FAILURES, resets on success.
    Callers check locked_until first; this never unlocks a locked pharmacy early."""
    ok = pin_ok(ph, pin)
    st = dict(ph.settings or {})
    if ok:
        st.pop("pin_failures", None)
        st.pop("pin_locked_until", None)
    else:
        st["pin_failures"] = st.get("pin_failures", 0) + 1
        if st["pin_failures"] >= MAX_PIN_FAILURES:
            st["pin_failures"] = 0
            st["pin_locked_until"] = (_now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
    ph.settings = st  # reassigned so SQLAlchemy sees the JSON change
    db.flush()
    return ok


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


def end_session(db: Session, token: str | None) -> None:
    """Sign out: the cookie value stops working at once."""
    row = db.get(m.OwnerSession, token) if token else None
    if row is not None:
        db.delete(row)
        db.flush()


def lender_for_key(db: Session, key: str | None) -> m.Lender | None:
    """The lender whose key this is, or None."""
    if not key:
        return None
    return db.scalar(select(m.Lender).where(m.Lender.api_key_sha256 == hash_key(key)))

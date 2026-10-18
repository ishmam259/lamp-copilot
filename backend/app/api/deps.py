"""Who is calling (win plan CORE-13). Applied at router level in routes.py, so no route
can forget its check.

- Owner routes (/pharmacies/{pid}/*): the owner session cookie for that pharmacy.
  No cookie → 401; a lender key instead → 403.
- Log routes (/logs*): any owner session.
- Lender routes (/lenders/{lid}/*): that lender's X-Lender-Key.
- Dev routes (/dev/*): 404 unless DEV_MODE is on.
"""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.engines import auth


@dataclass
class Caller:
    role: str          # "owner" or "lender"
    pharmacy_id: str | None = None
    lender_id: str | None = None


def _no_owner(db: Session, request: Request) -> HTTPException:
    if auth.lender_for_key(db, request.headers.get("x-lender-key")) is not None:
        return HTTPException(403, "Lenders can't use owner routes")
    return HTTPException(401, "Owner session required: unlock with the PIN")


def require_owner(pid: str, request: Request, db: Session = Depends(get_db)) -> Caller:
    """The owner of this pharmacy, from the session cookie."""
    s = auth.session_for(db, request.cookies.get(auth.SESSION_COOKIE))
    if s is None:
        raise _no_owner(db, request)
    if s.pharmacy_id != pid:
        raise HTTPException(403, "This session belongs to another pharmacy")
    return Caller("owner", pharmacy_id=pid)


def require_any_owner(request: Request, db: Session = Depends(get_db)) -> Caller:
    """Any signed-in owner (the audit log routes have no pharmacy in the path)."""
    s = auth.session_for(db, request.cookies.get(auth.SESSION_COOKIE))
    if s is None:
        raise _no_owner(db, request)
    return Caller("owner", pharmacy_id=s.pharmacy_id)


def require_lender(lid: str, db: Session = Depends(get_db),
                   x_lender_key: str | None = Header(default=None)) -> Caller:
    """The lender named in the path, from its key."""
    lender = auth.lender_for_key(db, x_lender_key)
    if lender is None:
        raise HTTPException(401, "Lender key required")
    if lender.id != lid:
        raise HTTPException(403, "This key belongs to another lender")
    return Caller("lender", lender_id=lid)


def dev_only() -> None:
    """Demo controls exist only with DEV_MODE=true."""
    if not settings.dev_mode:
        raise HTTPException(404, "Not Found")

"""Simulated lenders: products, per-lender consent, inbox and decisions."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import ApplicationOut, ConsentIn, ConsentOut, LenderOut

from .common import as_of, get_pharmacy
from .logbus import log

MAX_DEFAULT_PROBABILITY = 0.05


def _now() -> datetime:
    return datetime.now(timezone.utc)


def list_lenders(db: Session) -> list[LenderOut]:
    """All simulated lenders with their products (APR, fee, min and max amount)."""
    out = []
    for l in db.scalars(select(m.Lender).order_by(m.Lender.id.desc())):
        out.append(LenderOut(id=l.id, name=l.name, kind=l.kind, products=[
            {"key": p.key, "label": p.label, "apr_pct": p.apr_pct, "fee_pct": p.fee_pct,
             "min_amount": p.min_amount, "max_amount": p.max_amount} for p in l.products]))
    return out


def active_consent(db: Session, pid: str, lender_id: str) -> m.Consent | None:
    """The pharmacy's unrevoked consent for this lender, or None."""
    return db.scalar(select(m.Consent).where(m.Consent.pharmacy_id == pid, m.Consent.lender_id == lender_id,
                                             m.Consent.revoked_at.is_(None)))


def _consent_out(c: m.Consent) -> ConsentOut:
    return ConsentOut(id=c.id, lender_id=c.lender_id, scopes=c.scopes, granted_at=c.granted_at)


def list_consents(db: Session, pid: str) -> list[ConsentOut]:
    """Active consents only."""
    get_pharmacy(db, pid)
    rows = db.scalars(select(m.Consent).where(m.Consent.pharmacy_id == pid, m.Consent.revoked_at.is_(None))
                      .order_by(m.Consent.granted_at))
    return [_consent_out(c) for c in rows]


def grant_consent(db: Session, pid: str, body: ConsentIn) -> ConsentOut:
    """One active consent per lender: granting again replaces the old one."""
    get_pharmacy(db, pid)
    if db.get(m.Lender, body.lender_id) is None:
        raise HTTPException(404, f"Unknown lender '{body.lender_id}'")
    old = active_consent(db, pid, body.lender_id)
    if old:
        old.revoked_at = _now()
    n = (db.scalar(select(func.count()).select_from(m.Consent)) or 0) + 1
    c = m.Consent(id=f"cns-{n}", pharmacy_id=pid, lender_id=body.lender_id, scopes=body.scopes, granted_at=_now())
    db.add(c)
    log("T1", "CONSENT", "consent_granted", db, consent=c.id, lender=body.lender_id, scopes=body.scopes)
    db.commit()
    return _consent_out(c)


def revoke_consent(db: Session, pid: str, consent_id: str) -> dict:
    """Revoke an active consent (sets revoked_at) and log it. 404 if not active."""
    c = db.get(m.Consent, consent_id)
    if c is None or c.pharmacy_id != pid or c.revoked_at is not None:
        raise HTTPException(404, f"Unknown consent '{consent_id}'")
    c.revoked_at = _now()
    log("T1", "CONSENT", "consent_revoked", db, consent=consent_id, lender=c.lender_id)
    db.commit()
    return {"status": "revoked", "id": consent_id}


def _app_out(db: Session, a: m.Application) -> ApplicationOut:
    from .passport import get_passport

    ph = get_pharmacy(db, a.pharmacy_id)
    return ApplicationOut(id=a.id, pharmacy_id=a.pharmacy_id, pharmacy_name=ph.name, lender_id=a.lender_id,
                          product_key=a.product_key, amount=a.amount, status=a.status,
                          passport=get_passport(db, a.pharmacy_id), decision=a.decision, created_at=a.created_at)


def inbox(db: Session, lender_id: str) -> list[ApplicationOut]:
    """Applications from pharmacies that currently consent to this lender."""
    if db.get(m.Lender, lender_id) is None:
        raise HTTPException(404, f"Unknown lender '{lender_id}'")
    apps = [a for a in db.scalars(select(m.Application).where(m.Application.lender_id == lender_id)
                                  .order_by(m.Application.created_at.desc()))
            if active_consent(db, a.pharmacy_id, lender_id)]
    log("T0", "LENDER", "inbox_viewed", db, lender=lender_id, applications=len(apps))
    db.commit()
    return [_app_out(db, a) for a in apps]


def decide(db: Session, lender_id: str, app_id: str) -> ApplicationOut:
    """Simulated lender rule: approve if the passport's default probability <= 0.05
    and the amount is within the product's limits. Payout is a sandbox reference
    SANDBOX-<LENDER>-<as_of yyyymmdd>-<application number>; the amount is added to
    the pharmacy's cash."""
    a = db.get(m.Application, app_id)
    if a is None or a.lender_id != lender_id:
        raise HTTPException(404, f"Unknown application '{app_id}'")
    if a.status != "pending":
        raise HTTPException(409, f"Application is already {a.status}")
    if active_consent(db, a.pharmacy_id, lender_id) is None:
        raise HTTPException(403, "The pharmacy no longer shares its passport with this lender")
    from .passport import get_passport

    p = get_passport(db, a.pharmacy_id).default_probability
    product = db.scalar(select(m.LenderProduct).where(m.LenderProduct.lender_id == lender_id,
                                                      m.LenderProduct.key == a.product_key))
    in_limits = product is not None and product.min_amount <= a.amount <= product.max_amount
    ph = get_pharmacy(db, a.pharmacy_id)
    if p <= MAX_DEFAULT_PROBABILITY and in_limits:
        ref = f"SANDBOX-{lender_id.upper()}-{as_of(ph):%Y%m%d}-{app_id.split('-')[1]}"
        a.status = "approved"
        a.decision = {"approved": True, "payout_ref": ref,
                      "reason": f"Default probability {p:.1%} is within the {MAX_DEFAULT_PROBABILITY:.0%} limit."}
        ph.cash_on_hand += a.amount
        from .wallet import record_payout

        record_payout(db, a.pharmacy_id, a.amount, ref, as_of(ph))
        log("T3", "LENDER", "application_approved", db, application=app_id, payout=ref, amount=a.amount)
        log("T3", "PAYOUT", "sandbox_payout", db, application=app_id, payout=ref, amount=a.amount)
    else:
        a.status = "declined"
        reason = (f"Default probability {p:.1%} is above the {MAX_DEFAULT_PROBABILITY:.0%} limit." if in_limits
                  else "The amount is outside this product's limits.")
        a.decision = {"approved": False, "payout_ref": None, "reason": reason}
        log("T3", "LENDER", "application_declined", db, application=app_id, reason=reason)
    db.commit()
    return _app_out(db, a)

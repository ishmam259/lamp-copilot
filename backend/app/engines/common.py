"""Shared helpers for the engines. Engines never read the real clock: every
date is relative to the pharmacy's settings.as_of_date."""

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m


def get_pharmacy(db: Session, pid: str) -> m.Pharmacy:
    """The pharmacy row, or HTTP 404 if the id is unknown."""
    ph = db.get(m.Pharmacy, pid)
    if ph is None:
        raise HTTPException(404, f"Unknown pharmacy '{pid}'")
    return ph


def as_of(ph: m.Pharmacy) -> date:
    """The pharmacy's fixed "today" (settings.as_of_date). Engines never read the real clock."""
    return date.fromisoformat(ph.settings["as_of_date"])


def margin(ph: m.Pharmacy) -> float:
    """Gross margin as a fraction: settings.gross_margin_pct / 100 (12% in the seed)."""
    return ph.settings["gross_margin_pct"] / 100


def r2(x: float) -> float:
    """Round to 2 decimals for money. Adding 0.0 turns -0.0 into 0.0."""
    return round(x + 0.0, 2)


def sales_days(db: Session, pid: str, today: date, period_days: int) -> list[m.SalesDay]:
    """Sales-book rows for the `period_days` days before today (today excluded)."""
    start = today - timedelta(days=period_days)
    return list(db.scalars(select(m.SalesDay).where(
        m.SalesDay.pharmacy_id == pid, m.SalesDay.date >= start, m.SalesDay.date < today)))


def invoices_since(db: Session, pid: str, start: date, end: date) -> list[m.Invoice]:
    """Invoices with start <= invoice_date <= end."""
    return list(db.scalars(select(m.Invoice).where(
        m.Invoice.pharmacy_id == pid, m.Invoice.invoice_date >= start, m.Invoice.invoice_date <= end)))

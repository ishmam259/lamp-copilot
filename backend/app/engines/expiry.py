"""Expiry engine: sales-rate inference, sellable quantities, expiry view and order trimming."""

import math
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import ExpiryOut, TrimOut

from .common import as_of, get_pharmacy, r2


def claimed_batch_nos(db: Session, pid: str) -> set[str]:
    """Batches already in a return claim: they can't be claimed again."""
    return set(db.scalars(select(m.ReturnClaim.batch_no).where(m.ReturnClaim.pharmacy_id == pid)))


def sales_rates(db: Session, pid: str, today: date, window_days: int = 90) -> dict[str, float]:
    """Boxes sold per day, per product.

    rate = total qty purchased in the `window_days` days before today / window_days.

    Assumption: stock levels are roughly stable over the window, so what the
    pharmacy bought is a fair proxy for what it sold. Products with no purchase
    history get rate 0.
    """
    start = today - timedelta(days=window_days)
    rows = db.execute(select(m.InvoiceLine.product, m.InvoiceLine.qty).join(m.Invoice).where(
        m.Invoice.pharmacy_id == pid, m.Invoice.invoice_date >= start, m.Invoice.invoice_date < today))
    totals: dict[str, float] = {}
    for product, qty in rows:
        totals[product] = totals.get(product, 0) + qty
    return {p: q / window_days for p, q in totals.items()}


def sellable_qty(qty: int, rate: float, days_to_expiry: int, buffer_days: int) -> tuple[int, int]:
    """Return (sellable_days, sellable_qty).

    sellable_days = max(0, days_to_expiry - buffer_days)  (shops stop selling
    `buffer_days` before expiry); sellable_qty = floor(min(qty, rate x sellable_days)).
    """
    days = max(0, days_to_expiry - buffer_days)
    return days, math.floor(round(min(qty, rate * days), 6))


def get_expiry(db: Session, pid: str, horizon_days: int = 60) -> ExpiryOut:
    """Stock batches expiring within `horizon_days` of as_of (already-expired ones excluded).

    return_eligible = days_left >= supplier.return_cutoff_days (claims must be filed at
    least that many days before expiry). at_risk_value = cost of all listed batches;
    return_eligible_value = cost of the eligible ones. Sorted by days_left, latest first.
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    rows = []
    for b in db.scalars(select(m.StockBatch).where(m.StockBatch.pharmacy_id == pid)):
        left = (b.expiry_date - today).days
        if 0 <= left <= horizon_days:
            rows.append({"product": b.product, "batch_no": b.batch_no, "expiry_date": b.expiry_date,
                         "days_left": left, "qty": b.qty, "cost_value": r2(b.qty * b.unit_cost),
                         "return_eligible": left >= b.supplier.return_cutoff_days, "supplier": b.supplier.name})
    rows.sort(key=lambda r: (-r["days_left"], r["batch_no"]))
    return ExpiryOut(horizon_days=horizon_days, batches=rows,
                     at_risk_value=r2(sum(r["cost_value"] for r in rows)),
                     return_eligible_value=r2(sum(r["cost_value"] for r in rows if r["return_eligible"])))


def get_trim(db: Session, pid: str, order_id: str) -> TrimOut:
    """Sellable quantity per planned-order line, and a trimmed order.

    For each line: rate from sales_rates (90-day purchases / 90),
    sellable_days = max(0, days_to_expiry - expiry_buffer_days),
    sellable_qty = floor(min(qty, rate x sellable_days)),
    at_risk_value = (qty - sellable_qty) x unit_cost,
    suggested_qty = sellable_qty when at_risk_value > 0, else qty.
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    order = db.get(m.PlannedOrder, order_id)
    if order is None or order.pharmacy_id != pid:
        raise HTTPException(404, f"Unknown order '{order_id}'")
    rates = sales_rates(db, pid, today)
    lines = []
    for l in order.lines:
        rate = rates.get(l.product, 0)
        days, sellable = sellable_qty(l.qty, rate, (l.expiry_date - today).days, ph.settings["expiry_buffer_days"])
        risk = (l.qty - sellable) * l.unit_cost
        lines.append({"product": l.product, "qty": l.qty, "unit_cost": l.unit_cost,
                      "sales_rate_per_day": round(rate, 2), "sellable_days": days, "sellable_qty": sellable,
                      "suggested_qty": sellable if risk > 0 else l.qty, "at_risk_value": r2(risk)})
    original = sum(l["qty"] * l["unit_cost"] for l in lines)
    suggested = sum(l["suggested_qty"] * l["unit_cost"] for l in lines)
    return TrimOut(order_id=order_id, lines=lines, original_total=r2(original),
                   suggested_total=r2(suggested), saving=r2(original - suggested))

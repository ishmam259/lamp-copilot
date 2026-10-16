"""Sales-rate inference and sellable quantities (the F2 subset of the expiry engine)."""

import math
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m


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

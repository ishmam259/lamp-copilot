"""Supplier-dues calendar."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import DuesOut

from .common import as_of, get_pharmacy, r2


def status_for(days_left: int) -> str:
    """overdue (< 0 days left), due_soon (0..7) or upcoming (> 7)."""
    return "overdue" if days_left < 0 else "due_soon" if days_left <= 7 else "upcoming"


def get_dues(db: Session, pid: str) -> DuesOut:
    """Unpaid supplier invoices plus planned orders, sorted by due date.

    amount = invoice total minus payments so far; days_left = due_date - as_of.
    Planned orders appear under their order reference (e.g. PO-A-1026).
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    items = []
    for inv in db.scalars(select(m.Invoice).where(m.Invoice.pharmacy_id == pid, m.Invoice.status == "unpaid")):
        owed = inv.total - sum(p.amount for p in inv.payments)
        if owed > 0:
            items.append((inv.supplier.name, inv.invoice_no, owed, inv.due_date))
    for o in db.scalars(select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid,
                                                     m.PlannedOrder.status == "planned")):
        items.append((o.supplier.name, o.ref, o.total, o.due_date))
    items.sort(key=lambda i: (i[3], i[1]))
    out = []
    for supplier, no, amount, due in items:
        left = (due - today).days
        out.append({"supplier": supplier, "invoice_no": no, "amount": r2(amount), "due_date": due,
                    "days_left": left, "status": status_for(left)})
    return DuesOut(items=out, total_due=r2(sum(i["amount"] for i in out)))

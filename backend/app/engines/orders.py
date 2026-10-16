"""Upcoming planned orders."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import OrderOut

from .common import get_pharmacy, r2


def list_orders(db: Session, pid: str) -> list[OrderOut]:
    """Planned orders sorted by due date; total = sum(qty x unit_cost)."""
    get_pharmacy(db, pid)
    orders = db.scalars(select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid,
                                                     m.PlannedOrder.status == "planned").order_by(m.PlannedOrder.due_date))
    return [OrderOut(id=o.id, supplier=o.supplier.name, due_date=o.due_date, total=r2(o.total),
                     lines=[{"product": l.product, "qty": l.qty, "unit_cost": l.unit_cost} for l in o.lines])
            for o in orders]

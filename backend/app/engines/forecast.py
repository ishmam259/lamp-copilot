"""30-day cash forecast and shortfall detection."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import ForecastOut

from .common import as_of, get_pharmacy, r2, sales_days


def get_forecast(db: Session, pid: str, days: int = 30) -> ForecastOut:
    """Day-by-day cash balance from as_of (day 0) for `days` days.

    Start: pharmacy.cash_on_hand at the start of as_of.
    Each day, in this order:
      1. inflow  = average daily cash receipts = sum(cash_sales + dues_collected) / 30
                   over the 30 days before as_of
      2. routine restock at average daily cost of sales = sales x (1 - margin) / 30
      3. named outflows: unpaid supplier invoices on their due date (overdue ones on
         day 0), scheduled expenses on their day of month, planned orders on their due date
    Shortfall: a named outflow (or the routine restock) that takes the balance below
    settings.cash_buffer. amount = the extra deficit it causes, i.e.
    min(outflow, cash_buffer - balance_after). Routine sales and restock are not listed
    in `items`; named moves are, as negative amounts.
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    buffer = ph.settings["cash_buffer"]
    hist = sales_days(db, pid, today, 30)
    receipts = sum(r.cash_sales + r.dues_collected for r in hist) / 30
    restock = sum(r.cash_sales + r.credit_sales for r in hist) * (100 - ph.settings["gross_margin_pct"]) / 100 / 30

    end = today + timedelta(days=days - 1)
    named: dict = {}

    def add(day, label, amount):
        named.setdefault(max(day, today), []).append((label, amount))

    for inv in db.scalars(select(m.Invoice).where(m.Invoice.pharmacy_id == pid, m.Invoice.status == "unpaid")):
        owed = inv.total - sum(p.amount for p in inv.payments)
        if owed > 0 and inv.due_date <= end:
            add(inv.due_date, f"{inv.supplier.name} invoice {inv.invoice_no}", owed)
    schedule = list(db.scalars(select(m.ExpenseSchedule).where(m.ExpenseSchedule.pharmacy_id == pid)))
    for o in db.scalars(select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid,
                                                     m.PlannedOrder.status == "planned")):
        if o.due_date <= end:
            add(o.due_date, f"{o.supplier.name} order", o.total)

    balance = ph.cash_on_hand
    out_days, shortfalls = [], []
    for i in range(days):
        day = today + timedelta(days=i)
        moves = list(named.get(day, [])) + [(e.category, e.amount) for e in schedule if e.day_of_month == day.day]
        before = balance
        balance += receipts - restock
        if before >= buffer > balance:
            shortfalls.append({"date": day, "amount": r2(buffer - balance), "cause": "Daily restock exceeds receipts"})
        for label, amount in moves:
            balance -= amount
            if balance < buffer:
                shortfalls.append({"date": day, "amount": r2(min(amount, buffer - balance)),
                                   "cause": f"{label} BDT {amount:,.0f}"})
        out_days.append({
            "date": day, "inflow": r2(receipts), "outflow": r2(restock + sum(a for _, a in moves)),
            "balance": r2(balance), "items": [{"label": l, "amount": r2(-a)} for l, a in moves],
        })
    return ForecastOut(start_cash=r2(ph.cash_on_hand), days=out_days, shortfalls=shortfalls)

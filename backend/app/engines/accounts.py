"""Accounts: P&L, stock days, patient-due days, supplier concentration,
slow movers and expiring value."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import AccountsOut

from .common import as_of, get_pharmacy, invoices_since, margin, r2, sales_days
from .expiry import sales_rates, sellable_qty


def get_accounts(db: Session, pid: str, period_days: int = 30) -> AccountsOut:
    """Formulas (window = the `period_days` days before as_of):

    - sales = sum(cash_sales + credit_sales)
    - gross_profit = sales x gross_margin_pct; overheads = sum(expenses); net_profit = gross_profit - overheads
    - stock_value = sum(qty x unit_cost) over stock batches
    - stock_days = stock_value / (sales x (1 - margin) / period_days), 1 decimal
      (cost of sales stands in for purchases at cost)
    - patient_due_days = patient_dues / (sales / period_days), 1 decimal
    - active_suppliers = suppliers with an invoice in the 90 days up to as_of
    - top_suppliers = top 5 by share of those 90 days' purchases
    - slow_movers = stock batches and planned-order lines whose sellable_qty < qty
    - expiring_value_60d = cost of batches expiring in 0..60 days
    Days with zero sales give stock_days and patient_due_days of 0.
    """
    ph = get_pharmacy(db, pid)
    today, mg = as_of(ph), margin(ph)
    rows = sales_days(db, pid, today, period_days)
    sales = sum(r.cash_sales + r.credit_sales for r in rows)
    overheads = sum(r.expenses for r in rows)
    gross_profit = sales * mg
    daily_cogs = sales * (1 - mg) / period_days

    batches = list(db.scalars(select(m.StockBatch).where(m.StockBatch.pharmacy_id == pid)))
    stock_value = sum(b.qty * b.unit_cost for b in batches)
    patient_dues = sum(db.scalars(select(m.PatientDue.amount).where(m.PatientDue.pharmacy_id == pid)))

    recent = invoices_since(db, pid, today - timedelta(days=90), today)
    by_supplier: dict[str, float] = {}
    for inv in recent:
        by_supplier[inv.supplier.name] = by_supplier.get(inv.supplier.name, 0) + inv.total
    purchases = sum(by_supplier.values())
    top = sorted(by_supplier.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

    rates = sales_rates(db, pid, today)
    buffer = ph.settings["expiry_buffer_days"]
    held = [(b.product, b.qty, b.unit_cost, b.expiry_date) for b in batches]
    for order in db.scalars(select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid,
                                                         m.PlannedOrder.status == "planned")):
        held += [(l.product, l.qty, l.unit_cost, l.expiry_date) for l in order.lines]
    slow = []
    for product, qty, cost, expiry in held:
        _, sellable = sellable_qty(qty, rates.get(product, 0), (expiry - today).days, buffer)
        if sellable < qty:
            slow.append({"product": product, "qty": qty, "sellable_qty": sellable,
                         "at_risk_value": r2((qty - sellable) * cost)})
    slow.sort(key=lambda s: -s["at_risk_value"])

    expiring = sum(b.qty * b.unit_cost for b in batches if 0 <= (b.expiry_date - today).days <= 60)

    return AccountsOut(
        period_days=period_days,
        sales=r2(sales),
        gross_margin_pct=ph.settings["gross_margin_pct"],
        gross_profit=r2(gross_profit),
        overheads=r2(overheads),
        net_profit=r2(gross_profit - overheads),
        stock_value=r2(stock_value),
        stock_days=round(stock_value / daily_cogs, 1) if daily_cogs else 0,
        patient_dues=r2(patient_dues),
        patient_due_days=round(patient_dues / (sales / period_days), 1) if sales else 0,
        active_suppliers=len(by_supplier),
        top_suppliers=[{"name": n, "share_pct": round(100 * v / purchases, 1)} for n, v in top],
        slow_movers=slow,
        expiring_value_60d=r2(expiring),
    )

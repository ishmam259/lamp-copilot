"""Credit passport: a Bayesian on-time payment record, a placeholder lender
default model, and the terms a lender could offer."""

import math
from datetime import timedelta

from scipy.stats import beta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m

from app.schemas import PassportOut, ShelfLifeBatch, ShelfLifeCreditOut
from app.schemas.common import ExplainRow

from .common import as_of, get_pharmacy, invoices_since, r2


def get_passport(db: Session, pid: str) -> PassportOut:
    """Formulas, over settled (paid) invoices dated in the 90 days up to as_of:

    - weight = 1.0 if supplier_confirmed else 0.5; on time = paid_on <= due_date
    - s = weighted on-time count, f = weighted late count
    - posterior Beta(1 + s, 1 + f); theta_mean = (1 + s) / (2 + s + f);
      theta_low_5pct = 5th percentile of the posterior
    - default_probability p = 1 / (1 + exp(-(-3.915 + 6.0 x late_share))), late_share = f / (s + f).
      This is a placeholder lender model, not a fitted one.
    - score = clip((theta_low - 0.50) / 0.45, 0, 1) x max(0, 1 - p / 0.10)
    - advance_rate_pct = 60 + 30 x score; partner_share_pct = 100 - 90 x score
    theta_low and p are rounded to 3 decimals first, and score is computed from
    those published values, so anyone can recompute it from the passport itself.
    Unpaid invoices have no outcome yet and are left out. No history gives the
    uniform prior Beta(1, 1) and late_share 0.
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    paid = [inv for inv in invoices_since(db, pid, today - timedelta(days=90), today) if inv.payments]
    paid.sort(key=lambda inv: (inv.due_date, inv.invoice_no))

    s = f = 0.0
    evidence = []
    for inv in paid:
        paid_on = max(p.paid_on for p in inv.payments)
        on_time = paid_on <= inv.due_date
        w = 1.0 if inv.supplier_confirmed else 0.5
        s, f = (s + w, f) if on_time else (s, f + w)
        evidence.append({"invoice_no": inv.invoice_no, "supplier": inv.supplier.name, "due_date": inv.due_date,
                         "paid_on": paid_on, "on_time": on_time, "supplier_confirmed": inv.supplier_confirmed})

    late_share = f / (s + f) if s + f else 0.0
    theta_low = round(float(beta.ppf(0.05, 1 + s, 1 + f)), 3)
    p = round(1 / (1 + math.exp(-(-3.915 + 6.0 * late_share))), 3)
    score = round(min(max((theta_low - 0.50) / 0.45, 0), 1) * max(0.0, 1 - p / 0.10), 3)
    return PassportOut(
        invoices_total=len(paid),
        paid_on_time=sum(e["on_time"] for e in evidence),
        confirmed_share=round(sum(e["supplier_confirmed"] for e in evidence) / len(paid), 3) if paid else 0,
        theta_mean=round((1 + s) / (2 + s + f), 3),
        theta_low_5pct=theta_low,
        default_probability=p,
        score=score,
        advance_rate_pct=round(60 + 30 * score, 1),
        partner_share_pct=round(100 - 90 * score, 1),
        evidence=evidence,
    )


def _with_explain(c: ShelfLifeCreditOut) -> ShelfLifeCreditOut:
    """The lender card's breakdown: purpose-blind need − stock that won't sell = financeable."""
    c.explain = [ExplainRow(**r) for r in [
        {"label": f"Cash short on {c.needed_by:%d %b}: what a usual lender would lend",
         "amount": c.counterfactual_purpose_blind, "op": "start"},
        {"label": "Order stock that won't sell before expiry", "amount": c.not_financed, "op": "-"},
        {"label": "LaMP lends at most", "amount": c.financeable, "op": "="},
    ]]
    return c


def get_shelf_life_credit(db: Session, pid: str) -> ShelfLifeCreditOut:
    """Shelf-life credit: the ineligible-inventory rule asset-based lenders use, computed per
    batch from the photographed invoices before the purchase.

    need = the first forecast shortfall before any trim (19,000 on 26 Oct), caused by the
    planned order due on or after that date. For each line of that order:
        sellable_qty = floor(min(qty, sales_rate × (days_to_expiry − 30-day buffer)))
        unsellable_value = (qty − sellable_qty) × unit_cost
    not_financed = Σ unsellable_value (10,800): stock that won't sell before expiry is not
    financed. financeable = max(0, need − not_financed) (8,200).
    counterfactual_purpose_blind = the need itself: what a lender that ignores the shelf
    would finance. It is a computed comparison, not a request anyone made.

    Once the owner approves the trim, the order and the forecast no longer show the
    untrimmed purchase, so the credit saved at trim time (before the change) is returned.
    """
    from .expiry import get_trim
    from .forecast import get_forecast

    trims = db.scalars(select(m.Action).where(m.Action.pharmacy_id == pid, m.Action.kind == "trim_order",
                                              m.Action.status == "executed").order_by(m.Action.created_at.desc()))
    for t in trims:
        saved = (t.result or {}).get("shelf_life_credit")
        order = db.get(m.PlannedOrder, saved["order_id"]) if saved and saved["order_id"] else None
        if order is not None and order.status == "planned":
            return _with_explain(ShelfLifeCreditOut(**saved))

    shortfalls = get_forecast(db, pid).shortfalls
    orders = list(db.scalars(select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid,
                                                          m.PlannedOrder.status == "planned")
                             .order_by(m.PlannedOrder.due_date)))
    if not shortfalls or not orders:
        need, needed_by = 0.0, as_of(get_pharmacy(db, pid))
        order = orders[0] if orders else None
    else:
        need, needed_by = shortfalls[0].amount, shortfalls[0].date
        order = next((o for o in orders if o.due_date >= needed_by), orders[0])
    if order is None:
        return ShelfLifeCreditOut(order_id="", needed_by=needed_by, counterfactual_purpose_blind=0, not_financed=0,
                                  financeable=0, reason="No planned order to finance.", batches=[])
    trim = get_trim(db, pid, order.id)
    batches = [ShelfLifeBatch(product=l.product, qty_ordered=l.qty, sellable_qty=l.sellable_qty,
                              unsellable_value=r2(l.at_risk_value)) for l in trim.lines]
    not_financed = r2(min(need, sum(b.unsellable_value for b in batches)))
    financeable = r2(max(0.0, need - not_financed))
    reason = (f"{not_financed:,.0f} of this order won't sell before expiry, so it isn't financed."
              if not_financed else "Every line of this order will sell before expiry.")
    return _with_explain(ShelfLifeCreditOut(order_id=order.id, needed_by=needed_by, counterfactual_purpose_blind=r2(need),
                              not_financed=not_financed, financeable=financeable, reason=reason, batches=batches))

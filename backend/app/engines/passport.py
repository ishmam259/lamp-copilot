"""Credit passport: a Bayesian on-time payment record, a placeholder lender
default model, and the terms a lender could offer."""

import math
from datetime import timedelta

from scipy.stats import beta
from sqlalchemy.orm import Session

from app.schemas import PassportOut

from .common import as_of, get_pharmacy, invoices_since


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

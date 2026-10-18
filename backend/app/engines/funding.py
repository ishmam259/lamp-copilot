"""Funding planner: rank every way to cover a cash need and pick the cheapest
path that is certain enough."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import FundingNeed, FundingPlanOut

from .common import as_of, get_pharmacy, r2
from .expiry import get_expiry, get_trim
from .forecast import get_forecast
from .passport import get_passport

EXTENSION_DAYS = 20
EXTENSION_MIN_ON_TIME = 0.85
FALLBACK_LEAD_DAYS = 3


def _bdt(x: float) -> str:
    return f"BDT {x:,.0f}"


def _loan_cost(amount: float, apr_pct: float, tenor_days: int) -> float:
    """Simple interest: amount x APR x tenor / 365."""
    return amount * apr_pct / 100 * tenor_days / 365


def _product(db: Session, key: str) -> m.LenderProduct:
    return db.scalar(select(m.LenderProduct).where(m.LenderProduct.key == key))


def get_funding_plan(db: Session, pid: str, need: FundingNeed | None = None) -> FundingPlanOut:
    """Options and a recommended plan for a need {amount, needed_by}.

    Default need: the first forecast shortfall after applying the suggested trims
    to every planned order. Options:
    - trim_order: the trim saving (cost 0, certain), eligible when at-risk value > 0
    - return_claims: return-eligible expiring stock (cost 0). It arrives as supplier
      credit, not cash, so it never counts towards a need before needed_by.
    - supplier_extension: 20 more days from the order's supplier (cost 0, uncertain),
      eligible when the supplier is verified and the on-time share is >= 0.85
    - wallet_loan: amount x APR x tenor / 365, eligible within min..max amount
    - bank_supplier_credit: fee_pct x the (trimmed) order total per 30 days, eligible
      with >= min_history_invoices settled invoices
    - bank_sme_loan: eligible only from min_amount and min_history_months of history
    Cost disclosure on each financing option: APR on the amount actually financed
    (amount_financed), tenor_days, and the cost of covering this gap in BDT and as a
    % of the need. Supplier credit finances the whole trimmed order (49,200) for 30
    days: APR 12.2%, cost 492 = 6.0% of the 8,200 gap. Different tenors stay visible.
    Plan: trims first. Then the cheapest eligible option that covers the need; if it
    is uncertain, add the cheapest certain one as a fallback at needed_by - 3 days.
    total_cost_bdt assumes the primary option works. naive_cost_bdt = a wallet loan
    for the untrimmed first shortfall.
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    orders = list(db.scalars(select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid,
                                                          m.PlannedOrder.status == "planned")
                             .order_by(m.PlannedOrder.due_date)))
    trims = {o.id: get_trim(db, pid, o.id) for o in orders}
    trimmed_totals = {oid: t.suggested_total for oid, t in trims.items()}
    saving = sum(t.saving for t in trims.values())

    if need is None:
        after = get_forecast(db, pid, order_totals=trimmed_totals).shortfalls
        need = (FundingNeed(amount=after[0].amount, needed_by=after[0].date) if after
                else FundingNeed(amount=0, needed_by=today))
    amount = need.amount
    passport = get_passport(db, pid)
    on_time_share = passport.paid_on_time / passport.invoices_total if passport.invoices_total else 0
    order = next((o for o in orders if o.due_date >= need.needed_by), orders[0] if orders else None)
    supplier = order.supplier if order else None
    order_total = trimmed_totals[order.id] if order else 0
    returns = get_expiry(db, pid).return_eligible_value

    options = []

    def opt(key, label, provider, amt, cost, apr, eligible, reason, speed, certainty, financed=None, tenor=None):
        """`financed`/`tenor` are the cost disclosure: what is actually financed and for how
        long. The cost of covering the gap is the option's cost; its share is cost / need."""
        disclosed = financed is not None and cost is not None
        options.append({"key": key, "label": label, "provider": provider, "amount": r2(amt),
                        "cost_bdt": None if cost is None else r2(cost), "apr_pct": apr, "eligible": eligible,
                        "reason": reason, "speed": speed, "certainty": certainty,
                        "amount_financed": r2(financed) if financed is not None else None, "tenor_days": tenor,
                        "cost_of_gap_bdt": r2(cost) if disclosed else None,
                        "cost_of_gap_pct_of_need": round(cost / amount * 100, 2) if disclosed and amount > 0 else None})

    if order:
        t = trims[order.id]
        risky = [l for l in t.lines if l.at_risk_value > 0]
        reason = (f"Only {risky[0].sellable_qty} of {risky[0].qty} boxes will sell before expiry." if risky
                  else "Every line will sell before expiry.")
        opt("trim_order", f"Trim the slow mover from {supplier.name}'s order", "Your order", saving, 0, None,
            saving > 0, reason, "Now", "certain")
    exp_suppliers = sorted({b.supplier for b in get_expiry(db, pid).batches if b.return_eligible})
    opt("return_claims", "Claim returns for expiring stock",
        "Suppliers " + " and ".join(s.removeprefix("Supplier ") for s in exp_suppliers) if exp_suppliers else "Suppliers",
        returns, 0, None, returns > 0,
        f"Arrives as supplier credit, not cash, so it doesn't count before {need.needed_by:%d %b}.",
        "1–2 weeks", "uncertain")
    if supplier:
        ok = supplier.verified and on_time_share >= EXTENSION_MIN_ON_TIME
        opt("supplier_extension", f"Ask {supplier.name} for {EXTENSION_DAYS} more days", supplier.name, amount, 0,
            None, ok, f"You paid {passport.paid_on_time} of {passport.invoices_total} invoices on time." if ok
            else f"Needs a verified supplier and at least {EXTENSION_MIN_ON_TIME:.0%} of invoices paid on time.",
            "1–3 days", "uncertain", financed=amount, tenor=EXTENSION_DAYS)

    w = _product(db, "wallet_loan")
    ok = w.min_amount <= amount <= w.max_amount
    opt("wallet_loan", "Mobile-wallet loan, 3 months", w.lender.name, amount,
        _loan_cost(amount, w.apr_pct, w.tenor_days) if ok else None, w.apr_pct, ok,
        f"Within the {_bdt(w.min_amount)}–{w.max_amount:,.0f} limit." if ok
        else f"Loans run from {_bdt(w.min_amount)} to {w.max_amount:,.0f}.", "Same day", "certain",
        financed=amount, tenor=w.tenor_days)

    b = _product(db, "bank_supplier_credit")
    ok = bool(order) and passport.invoices_total >= b.min_history_invoices and b.min_amount <= order_total <= b.max_amount
    opt("bank_supplier_credit", f"Bank pays {supplier.name if supplier else 'the supplier'} now, you repay in 30 days",
        b.lender.name, order_total, order_total * b.fee_pct / 100 * b.tenor_days / 30 if ok else None,
        round(b.fee_pct * 365 / b.tenor_days, 1), ok,
        f"{b.fee_pct:g}% of the order for {b.tenor_days} days." if ok
        else f"Needs at least {b.min_history_invoices} paid invoices of history.", "2–3 days", "certain",
        financed=order_total, tenor=b.tenor_days)  # the bank finances the whole order to cover the gap

    sme = _product(db, "bank_sme_loan")
    first = db.scalar(select(m.Invoice.invoice_date).where(m.Invoice.pharmacy_id == pid)
                      .order_by(m.Invoice.invoice_date))
    months = (today - first).days // 30 if first else 0
    ok = amount >= sme.min_amount and months >= sme.min_history_months
    opt("bank_sme_loan", "Bank small-business loan", sme.lender.name, amount,
        _loan_cost(amount, sme.apr_pct, sme.tenor_days) if ok else None, sme.apr_pct if ok else None, ok,
        "Eligible." if ok else f"Minimum loan is {_bdt(sme.min_amount)}, with {sme.min_history_months} months of history.",
        "2–4 weeks", "certain", financed=amount, tenor=sme.tenor_days)

    steps, total = [], 0.0
    by_key = {o["key"]: o for o in options}
    if "trim_order" in by_key and by_key["trim_order"]["eligible"]:
        t = trims[order.id]
        for l in (l for l in t.lines if l.at_risk_value > 0):
            steps.append({"action_kind": "trim_order", "amount": l.at_risk_value, "when": today,
                          "label": f"Cut {l.product.split(' ')[0]} from {l.qty} to {l.suggested_qty} boxes"})
    if amount > 0:
        cover = [o for o in options if o["eligible"] and o["key"] not in ("trim_order", "return_claims")
                 and o["amount"] >= amount and o["cost_bdt"] is not None]
        cover.sort(key=lambda o: (o["cost_bdt"], o["certainty"] != "certain"))
        kinds = {"supplier_extension": "extension_request"}
        if cover:
            primary = cover[0]
            steps.append(_step(primary, kinds.get(primary["key"], "loan_application"), amount, today))
            total = primary["cost_bdt"]
            if primary["certainty"] == "uncertain":
                sure = next((o for o in cover if o["certainty"] == "certain"), None)
                if sure:
                    when = max(today, need.needed_by - timedelta(days=FALLBACK_LEAD_DAYS))
                    step = _step(sure, "loan_application", amount, when)
                    step["label"] = f"If {primary['provider']} hasn't agreed, {step['label'][0].lower()}{step['label'][1:]}"
                    steps.append({**step, "fallback_for": kinds.get(primary["key"], "loan_application")})

    first_raw = get_forecast(db, pid).shortfalls
    naive = _loan_cost(first_raw[0].amount, w.apr_pct, w.tenor_days) if first_raw else 0
    return FundingPlanOut(need=need, options=options, plan={"steps": steps, "total_cost_bdt": r2(total)},
                          naive_cost_bdt=r2(naive))


def _step(option: dict, kind: str, amount: float, when: date) -> dict:
    if option["key"] == "supplier_extension":
        label = f"Ask {option['provider']} for {EXTENSION_DAYS} more days on {_bdt(amount)}"
    elif option["key"] == "wallet_loan":
        label = "Take a mobile-wallet loan"
    else:
        label = option["label"]
    return {"action_kind": kind, "label": label, "amount": r2(amount), "when": when}

"""Owner policy (win plan CORE-08): the Pause switch.

While LaMP is paused, the copilot ("agent") and the follow-up runner ("lamp-scheduler")
can't propose anything, and actions they proposed earlier can't be approved. The owner's
own proposals and approvals still work. The state lives in pharmacy settings; only the
owner's HTTP route changes it (the chat can read it, never set it).
"""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas import PauseOut

from .common import get_pharmacy
from .logbus import log

AUTOMATED = {"agent", "lamp-scheduler"}


def get_pause(db: Session, pid: str) -> PauseOut:
    """Whether LaMP is paused for this pharmacy, and since when."""
    s = get_pharmacy(db, pid).settings or {}
    return PauseOut(paused=bool(s.get("paused")), changed_at=s.get("paused_changed_at"))


def set_pause(db: Session, pid: str, paused: bool) -> PauseOut:
    """Owner only (the route checks the session). Logged as agent_paused / agent_resumed."""
    ph = get_pharmacy(db, pid)
    now = datetime.now(timezone.utc)
    ph.settings = {**(ph.settings or {}), "paused": paused, "paused_changed_at": now.isoformat()}
    log("T1", "POLICY", "agent_paused" if paused else "agent_resumed", db, pharmacy=pid)
    if not paused:
        from .followups import retry_held

        retry_held(db, pid)
    db.commit()
    return PauseOut(paused=paused, changed_at=now)


def check_can_propose(db: Session, pid: str, proposed_by: str) -> None:
    """409 if LaMP is paused and the proposer is automated."""
    if proposed_by in AUTOMATED and get_pause(db, pid).paused:
        log("T1", "POLICY", "proposal_refused_paused", db, by=proposed_by)
        db.commit()
        raise HTTPException(409, "LaMP is paused by the owner: no new proposals from the copilot")


def check_can_approve(db: Session, pid: str, proposed_by: str) -> None:
    """409 if LaMP is paused and the action came from the copilot or the scheduler."""
    if proposed_by in AUTOMATED and get_pause(db, pid).paused:
        log("T1", "POLICY", "approval_refused_paused", db, by=proposed_by)
        db.commit()
        raise HTTPException(409, "LaMP is paused: resume it before approving what the copilot proposed")


# --- Borrowing ceiling (win plan CORE-07) ---------------------------------------------------
#
# Debt burden ratio (DBR): monthly loan repayment / monthly net cash flow. The cap is the
# closest published Bangladeshi numeric benchmark, applied to the pharmacy's cash flow; it is
# a consumer-financing rule, not an SME-specific one.
DBR_CAP_PCT = 35.0
DBR_SOURCE = {
    "title": "Prudential Regulations for Consumer Financing",
    "issuer": "Bangladesh Bank",
    "edition": "First Edition, 2004",
    "clause": "Unsecured Personal Loan PPG Guideline No. 12 - Debt Burden Ratio (DBR %): "
              "a maximum of 35% based on Net Monthly Income",
    "page": 65,
    "principle": "Regulation 3: total instalments must be commensurate with the borrower's "
                 "take-home/disposable income and repayment capacity",
    "file": "seed/sources/bangladesh_bank_prudential_regulations_consumer_financing_2004.pdf",
    "url": "https://www.bb.org.bd/mediaroom/circulars/brpd/pgfcf.pdf",
}


def monthly_net_cash_flow(db: Session, pid: str) -> float:
    """Net profit of the last 30 days (sales × margin − overheads): 13,500 for the seed."""
    from .accounts import get_accounts

    return get_accounts(db, pid).net_profit


def loan_dbr(db: Session, pid: str, lender_id: str, product_key: str, amount: float) -> dict | None:
    """Equal monthly instalments for this loan and their share of monthly net cash flow.

    total = amount + cost, where cost = amount × APR × tenor/365 (or fee% × tenor/30);
    months = max(1, round(tenor / 30)); monthly_repayment = total / months;
    dbr_pct = monthly_repayment / monthly net cash flow × 100.
    None when the product is unknown or the amount is outside its limits (the executor
    reports those)."""
    from sqlalchemy import select

    from app.db import models as m

    p = db.scalar(select(m.LenderProduct).where(m.LenderProduct.lender_id == lender_id,
                                                m.LenderProduct.key == product_key))
    if p is None or not p.min_amount <= amount <= p.max_amount:
        return None
    if p.apr_pct is not None:
        cost = amount * p.apr_pct / 100 * p.tenor_days / 365
    else:
        cost = amount * (p.fee_pct or 0) / 100 * p.tenor_days / 30
    months = max(1, round(p.tenor_days / 30))
    monthly = (amount + cost) / months
    ncf = monthly_net_cash_flow(db, pid)
    dbr = monthly / ncf * 100 if ncf > 0 else float("inf")
    return {"amount": round(amount, 2), "months": months, "monthly_repayment": round(monthly, 2),
            "monthly_net_cash_flow": round(ncf, 2), "dbr_pct": round(dbr, 1) if ncf > 0 else None,
            "cap_pct": DBR_CAP_PCT, "ok": dbr <= DBR_CAP_PCT}


def check_borrowing_ceiling(db: Session, pid: str, kind: str, payload: dict) -> None:
    """409 for a loan proposal whose monthly repayment exceeds 35% of monthly net cash flow."""
    if kind != "loan_application":
        return
    r = loan_dbr(db, pid, payload.get("lender_id", "wallet-lender"), payload.get("product_key", "wallet_loan"),
                 float(payload.get("amount") or 0))
    if r is None or r["ok"]:
        return
    log("T3", "POLICY", "loan_refused_dbr", db, amount=r["amount"], monthly_repayment=r["monthly_repayment"],
        monthly_net_cash_flow=r["monthly_net_cash_flow"], dbr_pct=r["dbr_pct"], cap_pct=DBR_CAP_PCT)
    db.commit()
    shown = f"{r['dbr_pct']}%" if r["dbr_pct"] is not None else "more than all"
    raise HTTPException(409, (
        f"Refused: the monthly repayment of BDT {r['monthly_repayment']:,.2f} would take {shown} of monthly net "
        f"cash flow (BDT {r['monthly_net_cash_flow']:,.0f}), above the {DBR_CAP_PCT:g}% cap. The cap follows "
        f"Bangladesh Bank's published debt-burden-ratio limit for unsecured personal loans ({DBR_SOURCE['title']}, "
        f"{DBR_SOURCE['edition']}, p. {DBR_SOURCE['page']}), applied to the pharmacy's cash flow."))


def get_policy(db: Session, pid: str):
    """The rules LaMP enforces, for the owner's read-only rules view."""
    from app.schemas import PolicyOut

    from .funding import get_funding_plan

    plan = get_funding_plan(db, pid)
    first = plan.need.amount
    naive = first + next((o.amount for o in plan.options if o.key == "trim_order" and o.eligible), 0)
    checks = []
    for label, amount in (("The plan's fallback loan", first), ("A loan for the untrimmed shortfall", naive)):
        r = loan_dbr(db, pid, "wallet-lender", "wallet_loan", amount)
        if r:
            checks.append({"label": label, **r})
    pause = get_pause(db, pid)
    return PolicyOut(paused=pause.paused, pin_required_for=["loan_application"], dbr_cap_pct=DBR_CAP_PCT,
                     monthly_net_cash_flow=round(monthly_net_cash_flow(db, pid), 2), source=DBR_SOURCE,
                     examples=checks)

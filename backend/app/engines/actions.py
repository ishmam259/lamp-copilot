"""Actions: the only way anything "happens".

States: proposed -> approved -> executed (or failed), or proposed -> rejected.
Anyone (the owner's UI or the copilot agent) may *propose*. Only the owner's
HTTP call POST /actions/{id}/approve reaches `execute_owner_approval`; the
agent's tools must never call it. Execution is deterministic and sandbox-only:
nothing leaves the system, no real money moves.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import ActionOut, ActionProposal

from . import registry
from .common import as_of, get_pharmacy, r2
from .expiry import get_expiry, get_trim
from .lenders import active_consent
from .logbus import log

EXTENSION_DAYS = 20


def _now() -> datetime:
    return datetime.now(timezone.utc)


def to_out(a: m.Action) -> ActionOut:
    """DB row to API shape. No calculation."""
    return ActionOut(id=a.id, kind=a.kind, status=a.status, payload=a.payload, proposed_by=a.proposed_by,
                     created_at=a.created_at, decided_at=a.decided_at, result=a.result,
                     requires_pin=requires_pin(a.kind))


PIN_KINDS = {"loan_application"}  # Tier 3: money from a lender


def requires_pin(kind: str) -> bool:
    """True if approving this kind of action must re-enter the owner PIN."""
    return kind in PIN_KINDS


def list_actions(db: Session, pid: str) -> list[ActionOut]:
    """Newest first."""
    get_pharmacy(db, pid)
    rows = db.scalars(select(m.Action).where(m.Action.pharmacy_id == pid).order_by(m.Action.created_at.desc(),
                                                                                    m.Action.id.desc()))
    return [to_out(a) for a in rows]


def _next_id(db: Session, model, prefix: str, width: int = 0) -> str:
    n = (db.scalar(select(func.count()).select_from(model)) or 0) + 1
    return f"{prefix}{n:0{width}d}" if width else f"{prefix}{n}"


def _check_payload(proposal: ActionProposal) -> None:
    """422 for an amount that isn't a non-negative number (it crashed the ceiling check).
    Unknown products and out-of-limit amounts still fail at execution, where they're logged."""
    amount = proposal.payload.get("amount")
    if amount is not None and (isinstance(amount, bool) or not isinstance(amount, int | float) or amount < 0):
        raise HTTPException(422, "payload.amount must be a number of BDT, zero or more")


def propose_action(db: Session, pid: str, proposal: ActionProposal, proposed_by: str) -> ActionOut:
    """Store a proposal. It does nothing until the owner approves it."""
    get_pharmacy(db, pid)
    if proposed_by not in ("owner", "agent", "lamp-scheduler"):
        raise HTTPException(422, "proposed_by must be 'owner', 'agent' or 'lamp-scheduler'")
    from .policy import check_borrowing_ceiling, check_can_propose

    check_can_propose(db, pid, proposed_by)
    _check_payload(proposal)
    check_borrowing_ceiling(db, pid, proposal.kind, proposal.payload)
    a = m.Action(id=_next_id(db, m.Action, "act-"), pharmacy_id=pid, kind=proposal.kind, status="proposed",
                 payload=proposal.payload, proposed_by=proposed_by, created_at=_now())
    db.add(a)
    log("T1", "ACTIONS", "action_proposed", db, action=a.id, kind=a.kind, by=proposed_by,
        amount=proposal.payload.get("amount"))
    db.commit()
    return to_out(a)


def _get(db: Session, pid: str, aid: str) -> m.Action:
    a = db.get(m.Action, aid)
    if a is None or a.pharmacy_id != pid:
        raise HTTPException(404, f"Unknown action '{aid}'")
    if a.status != "proposed":
        raise HTTPException(409, f"Action is already {a.status}")
    return a


def reject_action(db: Session, pid: str, aid: str) -> ActionOut:
    """Owner rejected: mark it rejected and log it. Nothing is executed."""
    a = _get(db, pid, aid)
    a.status, a.decided_at = "rejected", _now()
    log("T1", "ACTIONS", "action_rejected", db, action=aid, kind=a.kind)
    db.commit()
    return to_out(a)


def execute_owner_approval(db: Session, pid: str, aid: str) -> ActionOut:
    """Owner approved: run the deterministic sandbox executor for this action.
    Called only from the HTTP approve endpoint."""
    a = _get(db, pid, aid)
    from .policy import check_can_approve

    check_can_approve(db, pid, a.proposed_by)
    a.status, a.decided_at = "approved", _now()
    log("T1", "ACTIONS", "action_approved_by_owner", db, action=aid, kind=a.kind)
    db.flush()
    savepoint = db.begin_nested()
    try:
        result = EXECUTORS[a.kind](db, pid, a)
        savepoint.commit()
        a.status, a.result = "executed", result
        log("T3" if a.kind == "loan_application" else "T2", "EXECUTOR", "action_executed", db, action=aid,
            kind=a.kind)
    except _Failed as f:
        savepoint.rollback()  # undo anything half-done, keep the approval
        a.status, a.result = "failed", {"reason": f.reason, "summary": f.summary}
        if f.reason == "duplicate_financing":
            log("T3", "REGISTRY", "lock_rejected", db, action=aid, **f.data)
        elif f.reason == "no_consent":
            log("T3", "CONSENT", "application_blocked_no_consent", db, action=aid, **f.data)
        log("T3" if a.kind == "loan_application" else "T2", "EXECUTOR", "action_failed", db, action=aid,
            kind=a.kind, reason=f.reason, **f.data)
    db.commit()
    return to_out(a)


class _Failed(Exception):
    def __init__(self, reason: str, summary: str, **data):
        self.reason, self.summary, self.data = reason, summary, data


def _order(db: Session, pid: str, payload: dict) -> m.PlannedOrder:
    oid = payload.get("order_id")
    q = select(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid, m.PlannedOrder.status == "planned")
    order = db.get(m.PlannedOrder, oid) if oid else db.scalar(q.order_by(m.PlannedOrder.due_date))
    if order is None or order.pharmacy_id != pid:
        raise _Failed("unknown_order", "There is no planned order to apply this to.")
    return order


def _trim_order(db: Session, pid: str, a: m.Action) -> dict:
    """Set every line of the order to its suggested quantity."""
    from .passport import get_shelf_life_credit

    order = _order(db, pid, a.payload)
    trim = get_trim(db, pid, order.id)
    if trim.saving <= 0:
        raise _Failed("nothing_to_trim", f"Every line of order {order.id} already sells before expiry.")
    # The shelf-life credit is defined on the order as photographed; keep it before the trim changes it.
    credit = get_shelf_life_credit(db, pid).model_dump(mode="json")
    before = order.total
    for line, t in zip(order.lines, trim.lines):
        line.qty = t.suggested_qty
    db.flush()
    log("T2", "ORDERS", "order_trimmed", db, order=order.id, **{"from": before, "to": order.total})
    return {"order_id": order.id, "old_total": r2(before), "new_total": r2(order.total),
            "shelf_life_credit": credit,
            "summary": f"{order.supplier.name} order is now BDT {order.total:,.0f}."}


def _return_claim(db: Session, pid: str, a: m.Action) -> dict:
    """File a return claim for return-eligible batches (all of them, or payload.batch_nos)."""
    wanted = set(a.payload.get("batch_nos") or [])
    batches = [b for b in get_expiry(db, pid).batches if b.return_eligible and (not wanted or b.batch_no in wanted)]
    claimed = set(db.scalars(select(m.ReturnClaim.batch_no).where(m.ReturnClaim.pharmacy_id == pid)))
    batches = [b for b in batches if b.batch_no not in claimed]
    if not batches:
        raise _Failed("nothing_to_claim", "No return-eligible batches are left to claim.")
    claim_id = _next_id(db, m.ReturnClaim, "CLM-", 4)
    for i, b in enumerate(batches):
        db.add(m.ReturnClaim(id=f"{claim_id}-{i + 1}", pharmacy_id=pid, action_id=a.id, supplier=b.supplier,
                             batch_no=b.batch_no, expected_credit=b.cost_value, created_at=_now()))
    credit = sum(b.cost_value for b in batches)
    db.flush()
    log("T2", "EXPIRY", "return_claim_sent", db, claim=claim_id, batches=[b.batch_no for b in batches], amount=credit)
    return {"claim_id": claim_id, "expected_credit": r2(credit), "batches": [b.batch_no for b in batches],
            "summary": f"Return sent. Suppliers should credit BDT {credit:,.0f}."}


def _extension_request(db: Session, pid: str, a: m.Action) -> dict:
    """Send the request (sandbox). The supplier's answer arrives later via
    POST /dev/simulate/supplier-reply."""
    order = _order(db, pid, a.payload)
    log("T2", "SUPPLIERS", "extension_requested", db, supplier=order.supplier.name, order=order.id,
        days=EXTENSION_DAYS, amount=a.payload.get("amount"))
    from .followups import create_for_extension

    create_for_extension(db, pid, a)
    return {"status": "awaiting_supplier", "order_id": order.id,
            "summary": f"Request sent. Waiting for {order.supplier.name}."}


def supplier_reply(db: Session, aid: str, outcome: str | bool) -> ActionOut:
    """Simulated supplier answer to an executed extension request: "accepted", "declined"
    or "no_reply" (no answer by the follow-up deadline). If accepted, the requested amount
    of the order is paid EXTENSION_DAYS later. Declined or no reply fires the plan's
    follow-up (the fallback proposal and a notification)."""
    if isinstance(outcome, bool):
        outcome = "accepted" if outcome else "declined"
    accepted = outcome == "accepted"
    a = db.get(m.Action, aid)
    if a is None or a.kind != "extension_request":
        raise HTTPException(404, f"No extension request '{aid}'")
    if a.status != "executed" or (a.result or {}).get("status") != "awaiting_supplier":
        raise HTTPException(409, "This request isn't waiting for a supplier reply")
    order = db.get(m.PlannedOrder, a.result["order_id"])
    amount = min(float(a.payload.get("amount") or order.total), order.total)
    if accepted:
        order.deferred_amount, order.deferred_days = amount, EXTENSION_DAYS
    name = order.supplier.name
    summary = {"accepted": f"{name} agreed: BDT {amount:,.0f} is now due {EXTENSION_DAYS} days later.",
               "declined": f"{name} said no to more days.",
               "no_reply": f"{name} didn't reply by the deadline."}[outcome]
    a.result = {**a.result, "status": outcome, "summary": summary}
    log("T2", "SUPPLIERS", {"accepted": "extension_accepted", "declined": "extension_declined",
                            "no_reply": "extension_no_reply"}[outcome], db, action=aid, supplier=name, amount=amount)
    from .followups import on_supplier_reply

    on_supplier_reply(db, a.pharmacy_id, a, outcome)
    db.commit()
    return to_out(a)


def _loan_application(db: Session, pid: str, a: m.Action) -> dict:
    """Needs an active consent for the lender, then locks every financed receivable
    in the registry, then creates the application in the lender's inbox.

    Financed receivables: payload.invoice_nos (unpaid invoices) if given, else the
    planned order the money is for (committed by order ref, total and due date).
    """
    lender_id = a.payload.get("lender_id", "wallet-lender")
    product_key = a.payload.get("product_key", "wallet_loan")
    product = db.scalar(select(m.LenderProduct).where(m.LenderProduct.lender_id == lender_id,
                                                      m.LenderProduct.key == product_key))
    if product is None:
        raise _Failed("unknown_product", f"{lender_id} has no product {product_key}.")
    amount = float(a.payload.get("amount") or 0)
    if not product.min_amount <= amount <= product.max_amount:
        raise _Failed("amount_out_of_range",
                      f"{product.label} runs from BDT {product.min_amount:,.0f} to {product.max_amount:,.0f}.")
    if active_consent(db, pid, lender_id) is None:
        raise _Failed("no_consent", "Share your passport with this lender first (Passport tab).", lender=lender_id)

    if a.payload.get("invoice_nos"):
        invs = list(db.scalars(select(m.Invoice).where(m.Invoice.pharmacy_id == pid,
                                                       m.Invoice.invoice_no.in_(a.payload["invoice_nos"]))))
        receivables = [(i.supplier_id, i.invoice_no, i.total, i.invoice_date) for i in invs]
    else:
        o = _order(db, pid, a.payload)
        receivables = [(o.supplier_id, o.ref, o.total, o.due_date)]
    if not receivables:
        raise _Failed("nothing_to_finance", "No invoice or order to finance.")

    app_id = _next_id(db, m.Application, "APP-", 4)
    db.add(m.Application(id=app_id, pharmacy_id=pid, action_id=a.id, lender_id=lender_id, product_key=product_key,
                         amount=amount, status="pending", created_at=_now()))
    db.flush()
    for supplier_id, ref, total, dt in receivables:
        c = registry.commitment(supplier_id, ref, pid, total, dt)
        if not registry.try_lock(db, c, app_id):
            raise _Failed("duplicate_financing", f"{ref} is already financed elsewhere, so it can't back this loan.",
                          commitment=c, invoice=ref)
        log("T3", "REGISTRY", "lock_acquired", db, commitment=c, invoice=ref, application=app_id)
    log("T3", "LENDER", "application_submitted", db, application=app_id, lender=lender_id, amount=amount)
    lender = db.get(m.Lender, lender_id)
    return {"application_id": app_id, "summary": f"Loan application sent to {lender.name}."}


def _set_aside(db: Session, pid: str, a: m.Action) -> dict:
    sid = _next_id(db, m.SetAside, "SA-", 4)
    amount = float(a.payload.get("amount") or 0)
    start = as_of(get_pharmacy(db, pid))
    db.add(m.SetAside(id=sid, pharmacy_id=pid, action_id=a.id, amount=amount, start=start, created_at=_now()))
    db.flush()
    log("T2", "CASH", "set_aside_scheduled", db, schedule=sid, amount=amount)
    return {"schedule_id": sid, "summary": "Daily set-aside scheduled."}


EXECUTORS = {
    "trim_order": _trim_order,
    "return_claim": _return_claim,
    "extension_request": _extension_request,
    "loan_application": _loan_application,
    "set_aside": _set_aside,
}


def get_action(db: Session, pid: str, aid: str) -> m.Action:
    """The action, or HTTP 404."""
    return _get(db, pid, aid)

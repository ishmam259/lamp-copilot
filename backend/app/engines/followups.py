"""Follow-through (win plan CORE-04): the plan keeps working after the owner approves it.

When an extension request is executed, LaMP stores a follow-up for the plan's fallback:
the loan_application step the funding planner put after it (or `payload.fallback`), due
by that step's date (needed_by - 3 days: Fri 23 Oct in the demo). When the supplier
declines or doesn't reply by then, the runner, which is deterministic code and not the
LLM, proposes the fallback with proposed_by="lamp-scheduler" and notifies the owner. The
proposal still needs the owner's approval and PIN. If an open proposal for the same loan
already exists (the copilot proposed it with the plan), it is reused, not duplicated.
While LaMP is paused nothing is proposed: the follow-up waits and fires when the owner
resumes. Follow-ups are database rows, so they survive a restart. Engines keep
settings.as_of_date.
"""

from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import ActionProposal, FollowUpOut

from .logbus import log, notify

OPEN_STATES = {"proposed", "approved", "executed"}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_out(f: m.FollowUp) -> FollowUpOut:
    return FollowUpOut(id=f.id, plan_action_id=f.plan_action_id, fallback_kind=f.fallback_kind,
                       fallback_payload=f.fallback_payload, amount=f.amount, deadline=f.deadline, status=f.status,
                       fired_action_id=f.fired_action_id, created_at=f.created_at)


def list_followups(db: Session, pid: str) -> list[FollowUpOut]:
    """Every follow-up of this pharmacy, oldest first."""
    rows = db.scalars(select(m.FollowUp).where(m.FollowUp.pharmacy_id == pid)
                      .order_by(m.FollowUp.created_at, m.FollowUp.id))
    return [to_out(f) for f in rows]


def create_for_extension(db: Session, pid: str, ext: m.Action) -> m.FollowUp | None:
    """Store the fallback of an executed extension request: payload.fallback if given,
    else the funding plan's loan step that is the fallback for the extension."""
    from .funding import get_funding_plan

    step = next((s for s in get_funding_plan(db, pid).plan.steps if s.fallback_for == "extension_request"), None)
    fb = ext.payload.get("fallback")
    if fb:
        payload = {"lender_id": fb.get("lender_id", "wallet-lender"),
                   "product_key": fb.get("product_key", "wallet_loan"), "amount": float(fb["amount"])}
        deadline = date.fromisoformat(str(fb["when"])) if fb.get("when") else (step.when if step else None)
    elif step is not None:
        payload = {"lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": step.amount}
        deadline = step.when
    else:
        return None
    if deadline is None:
        return None
    n = (db.scalar(select(func.count()).select_from(m.FollowUp)) or 0) + 1
    f = m.FollowUp(id=f"fu-{n}", pharmacy_id=pid, plan_action_id=ext.id, fallback_kind="loan_application",
                   fallback_payload=payload, amount=payload["amount"], deadline=deadline, status="waiting",
                   created_at=_now())
    db.add(f)
    db.flush()
    log("T2", "FOLLOWUP", "followup_scheduled", db, followup=f.id, watches=ext.id, amount=f.amount,
        deadline=deadline, fallback="loan_application")
    return f


def on_supplier_reply(db: Session, pid: str, ext: m.Action, outcome: str) -> None:
    """Accepted → cancel the follow-ups. Declined or no reply → fire them."""
    waiting = db.scalars(select(m.FollowUp).where(m.FollowUp.plan_action_id == ext.id,
                                                  m.FollowUp.status == "waiting"))
    for f in list(waiting):
        if outcome == "accepted":
            f.status = "cancelled"
            log("T2", "FOLLOWUP", "followup_cancelled", db, followup=f.id, reason="supplier_accepted")
        else:
            f.trigger = outcome
            fire(db, pid, f)


def fire(db: Session, pid: str, f: m.FollowUp) -> None:
    """Propose the fallback as lamp-scheduler (or reuse an open proposal for the same loan)
    and notify the owner. While paused, wait."""
    from .actions import propose_action
    from .funding import get_funding_plan
    from .policy import get_pause

    if get_pause(db, pid).paused:
        log("T2", "FOLLOWUP", "followup_held_paused", db, followup=f.id, trigger=f.trigger)
        return
    open_loans = db.scalars(select(m.Action).where(m.Action.pharmacy_id == pid, m.Action.kind == f.fallback_kind,
                                                   m.Action.status.in_(OPEN_STATES))
                            .order_by(m.Action.created_at.desc(), m.Action.id.desc()))
    existing = next((a for a in open_loans if float(a.payload.get("amount") or 0) == f.amount), None)
    if existing is not None:
        action_id = existing.id
    else:
        why = "declined" if f.trigger == "declined" else f"didn't reply by {f.deadline:%a %d %b}"
        try:
            action_id = propose_action(db, pid, ActionProposal(kind=f.fallback_kind, payload={
                **f.fallback_payload, "summary": "Backup plan: mobile-wallet loan",
                "reason": f"The supplier {why}."}), "lamp-scheduler").id
        except HTTPException:  # paused in between
            log("T2", "FOLLOWUP", "followup_held_paused", db, followup=f.id, trigger=f.trigger)
            return
    f.status, f.fired_action_id = "fired", action_id
    log("T2", "FOLLOWUP", "followup_fired", db, followup=f.id, trigger=f.trigger, action=action_id, amount=f.amount)
    cost = next((o.cost_bdt for o in get_funding_plan(db, pid).options
                 if o.key == f.fallback_payload.get("product_key")), None)
    who = "didn't reply" if f.trigger == "no_reply" else "declined"
    body = (f"Backup plan ready: BDT {f.amount:,.0f} mobile-wallet loan"
            + (f", cost BDT {cost:,.2f}" if cost is not None else "") + ". Approve it with your PIN.")
    notify("owner", f"Supplier {who} the extension" if who == "declined" else "Supplier didn't reply",
           body, "/actions", db)


def retry_held(db: Session, pid: str) -> None:
    """After the owner resumes LaMP: fire follow-ups whose trigger came while paused."""
    held = db.scalars(select(m.FollowUp).where(m.FollowUp.pharmacy_id == pid, m.FollowUp.status == "waiting",
                                               m.FollowUp.trigger.is_not(None)))
    for f in list(held):
        fire(db, pid, f)

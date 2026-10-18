"""The copilot chat's tools: thin wrappers around the engines.

Every tool is read-only except `propose_action`, which only stores a proposal
with proposed_by="agent". Nothing here approves, executes, transfers money or
contacts anyone; app/agents/permissions.py lists the tiers and
tests/agents/test_security.py checks this list.

Tools return plain JSON-able dicts, so the model sees exactly the engine output.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from pydantic_ai import RunContext, Tool
from sqlalchemy.orm import Session

from app import engines
from app.schemas import ActionProposal, FundingNeed

from .permissions import PROPOSABLE_KINDS


@dataclass
class ChatDeps:
    db: Session
    pharmacy_id: str


def _json(x: Any) -> Any:
    if isinstance(x, list):
        return [_json(i) for i in x]
    return x.model_dump(mode="json") if hasattr(x, "model_dump") else x


def get_accounts(ctx: RunContext[ChatDeps], period_days: int = 30) -> dict:
    """Profit and loss for the last `period_days` days: sales, gross profit, overheads, net profit,
    stock value and days, patient dues (totals only), active suppliers, slow movers, expiring value."""
    return _json(engines.get_accounts(ctx.deps.db, ctx.deps.pharmacy_id, period_days))


def get_dues(ctx: RunContext[ChatDeps]) -> dict:
    """Supplier-dues calendar: every unpaid invoice and planned order, with due date and status."""
    return _json(engines.get_dues(ctx.deps.db, ctx.deps.pharmacy_id))


def get_forecast(ctx: RunContext[ChatDeps], days: int = 30) -> dict:
    """Day-by-day cash forecast and any shortfalls (date, amount, cause). Only the shortfalls and
    the days with named payments are returned, to keep the answer short."""
    fc = _json(engines.get_forecast(ctx.deps.db, ctx.deps.pharmacy_id, days))
    named = [d for d in fc["days"] if d["items"]]
    return {"start_cash": fc["start_cash"], "shortfalls": fc["shortfalls"], "days_with_payments": named,
            "closing_balance_last_day": fc["days"][-1]["balance"] if fc["days"] else fc["start_cash"]}


def get_alerts(ctx: RunContext[ChatDeps]) -> list:
    """Current alerts: shortfalls, expiring stock, return windows, old patient dues, suspicious documents."""
    return _json(engines.get_alerts(ctx.deps.db, ctx.deps.pharmacy_id))


def get_expiry(ctx: RunContext[ChatDeps], horizon_days: int = 60) -> dict:
    """Stock batches expiring within `horizon_days`, their cost, and how much can still be returned."""
    return _json(engines.get_expiry(ctx.deps.db, ctx.deps.pharmacy_id, horizon_days))


def get_orders(ctx: RunContext[ChatDeps]) -> list:
    """Upcoming planned supplier orders with their lines and due dates."""
    return _json(engines.list_orders(ctx.deps.db, ctx.deps.pharmacy_id))


def get_trim(ctx: RunContext[ChatDeps], order_id: str) -> dict:
    """For one planned order: how much of each line will sell before expiry, and the suggested smaller order."""
    return _json(engines.get_trim(ctx.deps.db, ctx.deps.pharmacy_id, order_id))


def get_funding_plan(ctx: RunContext[ChatDeps], amount: float | None = None, needed_by: date | None = None) -> dict:
    """Everything needed to answer "can I pay this order?": the first forecast shortfall before any
    trims, the suggested order trims, then ranked ways to cover what is left (cheapest first) and the
    recommended plan with a fallback. Leave both arguments empty for the next shortfall after trims."""
    db, pid = ctx.deps.db, ctx.deps.pharmacy_id
    need = None
    if amount is not None or needed_by is not None:
        default = engines.get_funding_plan(db, pid).need
        need = FundingNeed(amount=amount if amount is not None else default.amount,
                           needed_by=needed_by or default.needed_by)
    out = _json(engines.get_funding_plan(db, pid, need))
    first = engines.get_forecast(db, pid).shortfalls
    out["shortfall_before_trims"] = _json(first[0]) if first else None
    out["order_trims"] = [{k: t[k] for k in ("order_id", "original_total", "suggested_total", "saving")}
                          for t in (_json(engines.get_trim(db, pid, o.id)) for o in engines.list_orders(db, pid))]
    return out


def get_passport(ctx: RunContext[ChatDeps]) -> dict:
    """The credit passport: invoices paid on time, the cautious on-time estimate, default probability,
    score and the advance rate a lender could offer. Invoice-level evidence is summarised."""
    p = _json(engines.get_passport(ctx.deps.db, ctx.deps.pharmacy_id))
    p["evidence"] = {"invoices": len(p["evidence"]), "late": [e for e in p["evidence"] if not e["on_time"]]}
    return p


def share_plan(ctx: RunContext[ChatDeps], steps: list[str]) -> dict:
    """Show the owner your plan as a short checklist before you start a multi-step answer,
    e.g. ["Check the cash forecast and options", "Propose the cheapest steps"]. 2 to 4 steps,
    a few words each. This reads no data and changes nothing."""
    return {"shown": True, "steps": len(steps)}


def propose_action(ctx: RunContext[ChatDeps],
                   kind: Literal["return_claim", "extension_request", "trim_order", "set_aside", "loan_application"],
                   amount: float | None = None, order_id: str | None = None, reason: str = "") -> dict:
    """Propose an action for the owner to approve in the Actions screen. This does NOT do it:
    nothing happens until the owner approves. Use amounts and order ids from tool results only."""
    if kind not in PROPOSABLE_KINDS:
        raise ValueError(f"Can't propose {kind!r}")
    payload: dict[str, Any] = {"reason": reason} if reason else {}
    if amount is not None:
        payload["amount"] = amount
    if order_id:
        payload["order_id"] = order_id
    a = engines.propose_action(ctx.deps.db, ctx.deps.pharmacy_id, ActionProposal(kind=kind, payload=payload), "agent")
    return {"action_id": a.id, "kind": a.kind, "status": a.status,
            "note": "Proposed only. The owner must approve it in Actions."}


# Every tool shares the request's database session, so they run one at a time, never in parallel.
TOOLS = [Tool(f, sequential=True) for f in (
    get_accounts, get_dues, get_forecast, get_alerts, get_expiry, get_orders, get_trim,
    get_funding_plan, get_passport, share_plan, propose_action)]

"""Audit log: every state change, action transition, registry lock and capture.

Events are stored in audit_log; the SSE endpoint streams new rows to the UI.
Tiers: T0 read-only/regulator views, T1 owner and extraction, T2 engines,
T3 lender and financial execution.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import LogEvent

TIERS = {"T0", "T1", "T2", "T3"}


def _jsonable(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_jsonable(x) for x in v]
    return v


def log(tier: str, component: str, event: str, db: Session | None = None, **data) -> None:
    """Record one event. Inside a request, pass `db`: the row is committed with the
    caller's transaction. Without `db` (e.g. from agents/), it is committed at once."""
    if tier not in TIERS:
        raise ValueError(f"Unknown tier {tier!r}")
    row = m.AuditLog(ts=datetime.now(timezone.utc), tier=tier, component=component.upper(),
                     event=event, data=_jsonable(data))
    if db is not None:
        db.add(row)
        db.flush()
        return
    from app.db.session import SessionLocal

    with SessionLocal() as own:
        own.add(row)
        own.commit()


def to_event(row: m.AuditLog) -> LogEvent:
    """Audit-log row to LogEvent. Naive timestamps are treated as UTC."""
    ts = row.ts if row.ts.tzinfo else row.ts.replace(tzinfo=timezone.utc)
    return LogEvent(id=f"lg-{row.id}", ts=ts, tier=row.tier, component=row.component, event=row.event,
                    data=row.data or {})


def events(db: Session, since: str | None = None, after_id: int = 0) -> list[LogEvent]:
    """Events in order. `since` is a log id ("lg-12") or an ISO timestamp."""
    q = select(m.AuditLog).order_by(m.AuditLog.id)
    if since and since.startswith("lg-") and since[3:].isdigit():
        after_id = max(after_id, int(since[3:]))
    elif since:
        q = q.where(m.AuditLog.ts > datetime.fromisoformat(since.replace("Z", "+00:00")).replace(tzinfo=None))
    if after_id:
        q = q.where(m.AuditLog.id > after_id)
    return [to_event(r) for r in db.scalars(q)]


def _value(v) -> str:
    if isinstance(v, list):
        return ",".join(_value(x) for x in v)
    if isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v):
        return v[:12] + "…"  # commitments are long hex strings
    return str(v)


def as_text(e: LogEvent) -> str:
    """`[2026-10-16T14:05:00Z] [T3:REGISTRY] lock_acquired commitment=8f9c… application=APP-0001`"""
    ts = e.ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fields = " ".join(f"{k}={_value(v)}" for k, v in e.data.items())
    return f"[{ts}] [{e.tier}:{e.component}] {e.event}" + (f" {fields}" if fields else "")

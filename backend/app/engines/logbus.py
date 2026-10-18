"""Audit log: every state change, action transition, registry lock and capture.

Events are stored in audit_log; the SSE endpoint streams new rows to the UI.
Tiers: T0 read-only/regulator views, T1 owner and extraction, T2 engines,
T3 lender and financial execution.

The log is a hash chain (win plan CORE-09): each row stores
hash = sha256(prev_hash + canonical(event)), with GENESIS before the first row.
Changing, inserting or deleting any row breaks every hash after it; verify() finds
the first bad row. The head hash, published outside the database, anchors the chain.
"""

import hashlib
import json

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import LogEvent, VerifyOut

TIERS = {"T0", "T1", "T2", "T3"}
GENESIS = "0" * 64


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
    row = m.AuditLog(ts=datetime.now(timezone.utc).replace(microsecond=0), tier=tier, component=component.upper(),
                     event=event, data=_jsonable(data))
    if db is not None:
        _chain(db, row)
        return
    from app.db.session import SessionLocal

    with SessionLocal() as own:
        _chain(own, row)
        own.commit()


def notify(audience: str, title: str, body: str, link: str | None = None, db: Session | None = None) -> None:
    """A notification for the owner's or the admin's screen (win plan CORE-06). It travels
    on the log stream as component NOTIFY, event "notify". The caller builds the text from
    engine numbers; a notification never approves anything."""
    log("T1", "NOTIFY", "notify", db, audience=audience, title=title, body=body, link=link)


def canonical(ts: datetime, tier: str, component: str, event: str, data: dict) -> str:
    """The exact text that is hashed: compact JSON with sorted keys and a UTC timestamp."""
    ts = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    return json.dumps({"ts": ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tier": tier,
                       "component": component, "event": event, "data": data},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def link(prev_hash: str, text: str) -> str:
    return hashlib.sha256((prev_hash + text).encode("utf-8")).hexdigest()


def _chain(db: Session, row: m.AuditLog) -> None:
    last = db.scalar(select(m.AuditLog.hash).order_by(m.AuditLog.id.desc()).limit(1))
    row.prev_hash = last or GENESIS
    row.hash = link(row.prev_hash, canonical(row.ts, row.tier, row.component, row.event, row.data))
    db.add(row)
    db.flush()


def verify(db: Session) -> VerifyOut:
    """Recompute the chain from GENESIS. first_bad_id is the first row that doesn't match."""
    prev, count = GENESIS, 0
    for row in db.scalars(select(m.AuditLog).order_by(m.AuditLog.id)):
        count += 1
        expect = link(prev, canonical(row.ts, row.tier, row.component, row.event, row.data or {}))
        if row.prev_hash != prev or row.hash != expect:
            return VerifyOut(intact=False, count=count, head_hash=None, first_bad_id=f"lg-{row.id}")
        prev = row.hash
    return VerifyOut(intact=True, count=count, head_hash=None if count == 0 else prev)


def as_record(row_event: LogEvent, prev_hash: str) -> dict:
    """One line of the verifiable JSONL trace."""
    return {"id": row_event.id, "ts": row_event.ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tier": row_event.tier, "component": row_event.component, "event": row_event.event,
            "data": row_event.data, "prev_hash": prev_hash, "hash": row_event.hash}


def to_event(row: m.AuditLog) -> LogEvent:
    """Audit-log row to LogEvent. Naive timestamps are treated as UTC."""
    ts = row.ts if row.ts.tzinfo else row.ts.replace(tzinfo=timezone.utc)
    return LogEvent(id=f"lg-{row.id}", ts=ts, tier=row.tier, component=row.component, event=row.event,
                    data=row.data or {}, hash=row.hash or None)


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
    line = f"[{ts}] [{e.tier}:{e.component}] {e.event}" + (f" {fields}" if fields else "")
    return line + (f" #{e.hash[:12]}" if e.hash else "")

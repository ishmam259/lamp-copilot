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

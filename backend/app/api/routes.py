"""REST endpoints (docs/PLAN.md section 4.1). Thin: all logic is in app.engines."""

import asyncio
import copy
import importlib
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app import engines
from app.db import models as m
from app.db.seed import apply_extraction, load_seed
from app.db.session import get_db
from app.engines import actions as action_engine
from app.engines import logbus
from app.schemas import (
    AccountsOut,
    ActionOut,
    ActionProposal,
    Alert,
    ApplicationOut,
    CaptureConfirm,
    CaptureOut,
    ConsentIn,
    ConsentOut,
    DuesOut,
    ExpiryOut,
    ExtractionResult,
    ForecastOut,
    FundingNeed,
    FundingPlanOut,
    FundingRequest,
    LenderOut,
    LogEvent,
    OrderOut,
    PassportOut,
    PharmacyOut,
    SupplierReply,
    TrimOut,
)

from . import examples as ex

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- Demo controls ------------------------------------------------------------------

@router.post("/dev/reset")
def dev_reset(with_demo_captures: bool = False, db: Session = Depends(get_db)) -> dict:
    """Wipe everything and reload the seed (plus the three demo captures if asked)."""
    pid = load_seed(db, with_demo_captures=with_demo_captures)
    return {"status": "ok", "pharmacy_id": pid, "with_demo_captures": with_demo_captures}


@router.post("/dev/simulate/supplier-reply", response_model=ActionOut)
def simulate_supplier_reply(body: SupplierReply, db: Session = Depends(get_db)):
    """Demo only: the supplier answers an extension request."""
    return engines.supplier_reply(db, body.action_id, body.accepted)


@router.get("/pharmacies/{pid}", response_model=PharmacyOut)
def get_pharmacy(pid: str, db: Session = Depends(get_db)):
    ph = engines.get_pharmacy(db, pid)
    return {"id": ph.id, "name": ph.name, "city": ph.city, "settings": ph.settings}


# --- Captures -------------------------------------------------------------------------

async def _extract(image: bytes, kind: str) -> dict:
    """Call Pritom's extractor if it exists, else return the example draft."""
    try:
        extraction = importlib.import_module("app.agents.extraction")
    except ImportError:
        return copy.deepcopy(ex.CAPTURE_INVOICE["extraction"])
    result = await extraction.extract(image, kind)
    return ExtractionResult.model_validate(result).model_dump(mode="json")


def _capture_out(cap: m.Capture) -> dict:
    return {"id": cap.id, "kind": cap.kind, "status": cap.status, "image_url": None, "extraction": cap.extraction}


@router.post("/pharmacies/{pid}/captures", response_model=CaptureOut)
async def create_capture(pid: str, file: UploadFile = File(...),
                         kind: Literal["invoice", "sales_page"] = Form(...), db: Session = Depends(get_db)):
    engines.get_pharmacy(db, pid)
    extraction = await _extract(await file.read(), kind)
    n = (db.scalar(select(func.count()).select_from(m.Capture)) or 0) + 1
    cap = m.Capture(id=f"cap-{n}", pharmacy_id=pid, kind=kind, status="needs_review",
                    extraction=extraction, created_at=datetime.now(timezone.utc))
    db.add(cap)
    suspicious = extraction.get("suspicious_text") or []
    engines.log("T1", "CAPTURE", "capture_created", db, capture=cap.id, kind=kind,
                model=extraction.get("model"), mode=extraction.get("mode"))
    if suspicious:
        engines.log("T1", "CAPTURE", "suspicious_text_flagged", db, capture=cap.id, count=len(suspicious))
    db.commit()
    return _capture_out(cap)


def _get_capture(db: Session, pid: str, cid: str) -> m.Capture:
    cap = db.get(m.Capture, cid)
    if cap is None or cap.pharmacy_id != pid:
        raise HTTPException(404, f"Unknown capture '{cid}'")
    return cap


@router.get("/pharmacies/{pid}/captures/{cid}", response_model=CaptureOut)
def get_capture(pid: str, cid: str, db: Session = Depends(get_db)):
    if cid == ex.CAPTURE_INVOICE["id"]:
        return ex.CAPTURE_INVOICE
    return _capture_out(_get_capture(db, pid, cid))


@router.post("/pharmacies/{pid}/captures/{cid}/confirm", response_model=CaptureOut)
def confirm_capture(pid: str, cid: str, body: CaptureConfirm, db: Session = Depends(get_db)):
    """Save the owner-corrected draft as an invoice (plus stock) or as sales days."""
    cap = _get_capture(db, pid, cid)
    if cap.status == "confirmed":
        raise HTTPException(409, "Capture is already confirmed")
    extraction = dict(cap.extraction)
    if body.invoice:
        extraction["invoice"] = body.invoice.model_dump(mode="json")
    if body.sales_page:
        extraction["sales_page"] = body.sales_page.model_dump(mode="json")
    apply_extraction(db, pid, extraction, capture_id=cid)
    cap.extraction, cap.status = extraction, "confirmed"
    engines.log("T1", "CAPTURE", "capture_confirmed", db, capture=cid, kind=cap.kind)
    db.commit()
    return _capture_out(cap)


# --- Read views (engines) ---------------------------------------------------------------

@router.get("/pharmacies/{pid}/accounts", response_model=AccountsOut)
def get_accounts(pid: str, period_days: int = 30, db: Session = Depends(get_db)):
    return engines.get_accounts(db, pid, period_days)


@router.get("/pharmacies/{pid}/dues", response_model=DuesOut)
def get_dues(pid: str, db: Session = Depends(get_db)):
    return engines.get_dues(db, pid)


@router.get("/pharmacies/{pid}/forecast", response_model=ForecastOut)
def get_forecast(pid: str, days: int = 30, db: Session = Depends(get_db)):
    return engines.get_forecast(db, pid, days)


@router.get("/pharmacies/{pid}/alerts", response_model=list[Alert])
def get_alerts(pid: str, db: Session = Depends(get_db)):
    return engines.get_alerts(db, pid)


@router.get("/pharmacies/{pid}/expiry", response_model=ExpiryOut)
def get_expiry(pid: str, horizon_days: int = 60, db: Session = Depends(get_db)):
    return engines.get_expiry(db, pid, horizon_days)


@router.get("/pharmacies/{pid}/orders", response_model=list[OrderOut])
def list_orders(pid: str, db: Session = Depends(get_db)):
    return engines.list_orders(db, pid)


@router.get("/pharmacies/{pid}/orders/{oid}/trim", response_model=TrimOut)
def get_trim(pid: str, oid: str, db: Session = Depends(get_db)):
    return engines.get_trim(db, pid, oid)


@router.post("/pharmacies/{pid}/funding-plan", response_model=FundingPlanOut)
def funding_plan(pid: str, body: FundingRequest | None = Body(default=None), db: Session = Depends(get_db)):
    if body is None or (body.amount is None and body.needed_by is None):
        return engines.get_funding_plan(db, pid)
    default = engines.get_funding_plan(db, pid).need
    need = FundingNeed(amount=default.amount if body.amount is None else body.amount,
                       needed_by=body.needed_by or default.needed_by)
    return engines.get_funding_plan(db, pid, need)


@router.get("/pharmacies/{pid}/passport", response_model=PassportOut)
def get_passport(pid: str, db: Session = Depends(get_db)):
    return engines.get_passport(db, pid)


# --- Actions: only this approve endpoint can approve ------------------------------------

@router.get("/pharmacies/{pid}/actions", response_model=list[ActionOut])
def list_actions(pid: str, db: Session = Depends(get_db)):
    return engines.list_actions(db, pid)


@router.post("/pharmacies/{pid}/actions", response_model=ActionOut)
def propose_action(pid: str, proposal: ActionProposal,
                   proposed_by: Literal["owner", "agent"] | None = None, db: Session = Depends(get_db)):
    by = proposal.proposed_by or proposed_by or "owner"
    return engines.propose_action(db, pid, proposal.model_copy(update={"proposed_by": None}), by)


@router.post("/pharmacies/{pid}/actions/{aid}/approve", response_model=ActionOut)
def approve_action(pid: str, aid: str, db: Session = Depends(get_db)):
    return action_engine.execute_owner_approval(db, pid, aid)


@router.post("/pharmacies/{pid}/actions/{aid}/reject", response_model=ActionOut)
def reject_action(pid: str, aid: str, db: Session = Depends(get_db)):
    return engines.reject_action(db, pid, aid)


# --- Consents and lenders ---------------------------------------------------------------

@router.get("/pharmacies/{pid}/consents", response_model=list[ConsentOut])
def list_consents(pid: str, db: Session = Depends(get_db)):
    return engines.list_consents(db, pid)


@router.post("/pharmacies/{pid}/consents", response_model=ConsentOut)
def grant_consent(pid: str, body: ConsentIn, db: Session = Depends(get_db)):
    return engines.grant_consent(db, pid, body)


@router.delete("/pharmacies/{pid}/consents/{consent_id}")
def revoke_consent(pid: str, consent_id: str, db: Session = Depends(get_db)) -> dict:
    return engines.revoke_consent(db, pid, consent_id)


@router.get("/lenders", response_model=list[LenderOut])
def list_lenders(db: Session = Depends(get_db)):
    return engines.list_lenders(db)


@router.get("/lenders/{lid}/applications", response_model=list[ApplicationOut])
def lender_inbox(lid: str, db: Session = Depends(get_db)):
    return engines.inbox(db, lid)


@router.post("/lenders/{lid}/applications/{appid}/decide", response_model=ApplicationOut)
def decide_application(lid: str, appid: str, db: Session = Depends(get_db)):
    return engines.decide(db, lid, appid)


# --- Audit log ----------------------------------------------------------------------------

@router.get("/logs", response_model=list[LogEvent])
def get_logs(since: str | None = None, db: Session = Depends(get_db)):
    """All events, or those after `since` (a log id like lg-12, or an ISO timestamp)."""
    return logbus.events(db, since)


@router.get("/logs/export", response_class=PlainTextResponse)
def export_logs(db: Session = Depends(get_db)) -> str:
    """The audit log as text, one line per event (the sandbox execution trace)."""
    return "\n".join(logbus.as_text(e) for e in logbus.events(db)) + "\n"


@router.get("/logs/stream")
async def stream_logs(once: bool = False, db: Session = Depends(get_db)):
    """Server-Sent Events: every past event, then new ones as they happen.
    `once=true` sends the backlog and closes (for tests)."""
    factory = sessionmaker(bind=db.get_bind())

    async def gen():
        last = 0
        while True:
            with factory() as s:
                batch = logbus.events(s, after_id=last)
            for e in batch:
                last = int(e.id[3:])
                yield f"id: {e.id}\ndata: {json.dumps(e.model_dump(mode='json'))}\n\n"
            if once:
                return
            yield ": keepalive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

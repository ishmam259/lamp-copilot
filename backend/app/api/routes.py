"""REST endpoints (docs/PLAN.md section 4.1). Thin: all logic is in app.engines."""

import asyncio
import importlib
import json
import math
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session, sessionmaker

from app import engines
from app.config import settings
from app.db import models as m
from app.db.seed import apply_extraction, load_seed
from app.db.session import get_db
from app.engines import actions as action_engine
from app.engines import auth, catalogue, followups, policy, value, wallet
from app.engines.common import as_of
from app.engines import logbus
from app.schemas import (
    AccountOut,
    AccountsOut,
    ActionOut,
    ActionProposal,
    ApprovalIn,
    Alert,
    ApplicationOut,
    CaptureConfirm,
    CaptureOut,
    CatalogueOut,
    ConsentIn,
    ConsentOut,
    ConsentPreview,
    DuesOut,
    ExpiryOut,
    ExtractionResult,
    FollowUpOut,
    ForecastOut,
    FundingNeed,
    FundingPlanOut,
    FundingRequest,
    LenderOut,
    LogEvent,
    OrderOut,
    PassportOut,
    PauseIn,
    PauseOut,
    PolicyOut,
    PharmacyOut,
    PharmacySettings,
    SessionIn,
    SessionOut,
    ShelfLifeCreditOut,
    SupplierReply,
    TrimOut,
    ValueOut,
    VerifyOut,
)

from . import examples as ex
from .deps import Caller, dev_only, require_any_owner, require_lender, require_owner

router = APIRouter()   # public: health, owner unlock, lender catalogue
owner = APIRouter()    # /pharmacies/{pid}/*: owner session for that pharmacy
lender = APIRouter()   # /lenders/{lid}/*: that lender's key
logs = APIRouter()     # /logs*: any owner session
dev = APIRouter()      # /dev/*: only with DEV_MODE=true


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- Demo controls ------------------------------------------------------------------

@dev.post("/dev/reset")
def dev_reset(with_demo_captures: bool | None = None, db: Session = Depends(get_db)) -> dict:
    """Wipe everything and reload the seed (plus the three demo captures if asked; when not
    given, DEMO_RESET_WITH_CAPTURES decides)."""
    if with_demo_captures is None:
        with_demo_captures = settings.demo_reset_with_captures
    pid = reset_demo(db, with_demo_captures)
    return {"status": "ok", "pharmacy_id": pid, "with_demo_captures": with_demo_captures}


def reset_demo(db: Session, with_demo_captures: bool) -> str:
    """Reload the seed, keeping owners signed in. Used by /dev/reset and the auto-reset."""
    try:
        sessions = [(s.token, s.pharmacy_id, s.created_at, s.expires_at) for s in db.scalars(select(m.OwnerSession))]
    except (OperationalError, ProgrammingError):  # brand-new database: no tables yet
        sessions = []
    # End this read transaction: on PostgreSQL its lock on owner_session would block the
    # DROP TABLE that load_seed runs on another connection.
    db.rollback()
    pid = load_seed(db, with_demo_captures=with_demo_captures)
    for token, sp, created, expires in sessions:
        if db.get(m.Pharmacy, sp) is not None:
            db.add(m.OwnerSession(token=token, pharmacy_id=sp, created_at=created, expires_at=expires))
    db.commit()
    return pid


@dev.post("/dev/simulate/supplier-reply", response_model=ActionOut)
def simulate_supplier_reply(body: SupplierReply, db: Session = Depends(get_db)):
    """Demo only: the supplier answers an extension request."""
    return engines.supplier_reply(db, body.action_id, body.resolved())


# --- Owner unlock -------------------------------------------------------------------------

@router.delete("/pharmacies/{pid}/session", status_code=204)
def end_session(pid: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """Lock the app: ends this session and clears the cookie. Safe to call when signed out."""
    s = auth.session_for(db, request.cookies.get(auth.SESSION_COOKIE))
    if s is not None and s.pharmacy_id == pid:
        auth.end_session(db, s.token)
        engines.log("T1", "AUTH", "owner_locked", db, pharmacy=pid)
        db.commit()
    response.delete_cookie(auth.SESSION_COOKIE, path="/")

def _refuse_if_locked(ph) -> None:
    until = auth.locked_until(ph)
    if until:
        minutes = max(1, math.ceil((until - auth._now()).total_seconds() / 60))
        raise HTTPException(429, f"Too many wrong PINs. Try again in {minutes} minute{'s' if minutes > 1 else ''}.")


@router.post("/pharmacies/{pid}/session", response_model=SessionOut)
def create_session(pid: str, body: SessionIn, response: Response, db: Session = Depends(get_db)):
    """The owner's PIN unlocks the app: sets the HttpOnly session cookie."""
    ph = engines.get_pharmacy(db, pid)
    _refuse_if_locked(ph)
    if not auth.check_pin(db, ph, body.pin):
        engines.log("T1", "AUTH", "unlock_failed", db, pharmacy=pid)
        db.commit()
        raise HTTPException(401, "Wrong PIN")
    s = auth.create_session(db, pid)
    engines.log("T1", "AUTH", "owner_unlocked", db, pharmacy=pid)
    db.commit()
    response.set_cookie(auth.SESSION_COOKIE, s.token, max_age=auth.SESSION_HOURS * 3600,
                        httponly=True, samesite="lax", path="/")
    return {"pharmacy_id": pid, "role": "owner", "expires_at": s.expires_at}


@owner.get("/pharmacies/{pid}", response_model=PharmacyOut)
def get_pharmacy(pid: str, db: Session = Depends(get_db)):
    ph = engines.get_pharmacy(db, pid)
    # Only the public fields: settings also holds the PIN hash, the PIN lockout and the Pause state.
    public = {k: v for k, v in (ph.settings or {}).items() if k in PharmacySettings.model_fields}
    return {"id": ph.id, "name": ph.name, "city": ph.city, "settings": public}


# --- Captures -------------------------------------------------------------------------

async def _extract(image: bytes, kind: str, db: Session, today=None) -> dict:
    """Read the photo with the extractor (it falls back to the example draft for an
    unrecorded photo in replay mode). A refused live call is a 503."""
    try:
        extraction = importlib.import_module("app.agents.extraction")
        from app.agents import llm
    except ImportError:
        return ex.fallback_extraction(kind)
    try:
        result = await extraction.extract(image, kind, db=db, today=today)
    except llm.BudgetExceeded as e:
        raise HTTPException(503, str(e))
    return ExtractionResult.model_validate(result).model_dump(mode="json")


def _capture_out(cap: m.Capture) -> dict:
    return {"id": cap.id, "kind": cap.kind, "status": cap.status, "image_url": None, "extraction": cap.extraction}


@owner.post("/pharmacies/{pid}/captures", response_model=CaptureOut)
async def create_capture(pid: str, file: UploadFile = File(...),
                         kind: Literal["invoice", "sales_page"] = Form(...), db: Session = Depends(get_db)):
    ph = engines.get_pharmacy(db, pid)
    extraction = await _extract(await file.read(), kind, db, today=as_of(ph))
    n = (db.scalar(select(func.count()).select_from(m.Capture)) or 0) + 1
    cap = m.Capture(id=f"cap-{n}", pharmacy_id=pid, kind=kind, status="needs_review",
                    extraction=extraction, created_at=datetime.now(timezone.utc))
    db.add(cap)
    suspicious = extraction.get("suspicious_text") or []
    engines.log("T1", "CAPTURE", "capture_created", db, capture=cap.id, kind=kind,
                model=extraction.get("model"), mode=extraction.get("mode"))
    if suspicious:
        engines.log("T1", "CAPTURE", "suspicious_text_flagged", db, capture=cap.id, count=len(suspicious))
        logbus.notify("owner", "A photo contained instructions",
                      f"LaMP ignored {len(suspicious)} line{'s' if len(suspicious) > 1 else ''} in this "
                      f"{kind.replace('_', ' ')} that gave it orders. Nothing was done. Check the "
                      f"{kind.replace('_', ' ')} before you save it.", f"/capture?id={cap.id}", db)
    db.commit()
    return _capture_out(cap)


def _get_capture(db: Session, pid: str, cid: str) -> m.Capture:
    cap = db.get(m.Capture, cid)
    if cap is None or cap.pharmacy_id != pid:
        raise HTTPException(404, f"Unknown capture '{cid}'")
    return cap


@owner.get("/pharmacies/{pid}/captures/{cid}", response_model=CaptureOut)
def get_capture(pid: str, cid: str, db: Session = Depends(get_db)):
    if cid == ex.CAPTURE_INVOICE["id"]:
        return ex.CAPTURE_INVOICE
    return _capture_out(_get_capture(db, pid, cid))


@owner.post("/pharmacies/{pid}/captures/{cid}/confirm", response_model=CaptureOut)
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
    # Save only the part that matches what was photographed.
    extraction["sales_page" if cap.kind == "invoice" else "invoice"] = None
    if not extraction.get(cap.kind):
        raise HTTPException(422, f"Nothing to save: the {cap.kind.replace('_', ' ')} draft is empty")
    apply_extraction(db, pid, extraction, capture_id=cid)
    cap.extraction, cap.status = extraction, "confirmed"
    engines.log("T1", "CAPTURE", "capture_confirmed", db, capture=cid, kind=cap.kind)
    fc = engines.get_forecast(db, pid)
    first = fc.shortfalls[0] if fc.shortfalls else None
    engines.log("T2", "FORECAST", "forecast_updated", db, first_shortfall_date=first.date if first else None,
                first_shortfall=first.amount if first else 0)
    db.commit()
    return _capture_out(cap)


# --- Read views (engines) ---------------------------------------------------------------

@owner.get("/pharmacies/{pid}/accounts", response_model=AccountsOut)
def get_accounts(pid: str, period_days: int = 30, db: Session = Depends(get_db)):
    return engines.get_accounts(db, pid, period_days)


@owner.get("/pharmacies/{pid}/account", response_model=AccountOut)
def get_account(pid: str, db: Session = Depends(get_db)):
    """Sandbox wallet balance and transactions, and the statement matched to the books."""
    return wallet.get_account(db, pid)


@owner.get("/pharmacies/{pid}/value", response_model=ValueOut)
def get_value(pid: str, db: Session = Depends(get_db)):
    """What the approved actions saved or recovered, each with its basis and counterfactual."""
    return value.get_value(db, pid)


@owner.get("/pharmacies/{pid}/dues", response_model=DuesOut)
def get_dues(pid: str, db: Session = Depends(get_db)):
    return engines.get_dues(db, pid)


@owner.get("/pharmacies/{pid}/forecast", response_model=ForecastOut)
def get_forecast(pid: str, days: int = 30, db: Session = Depends(get_db)):
    return engines.get_forecast(db, pid, days)


@owner.get("/pharmacies/{pid}/alerts", response_model=list[Alert])
def get_alerts(pid: str, db: Session = Depends(get_db)):
    return engines.get_alerts(db, pid)


@owner.get("/pharmacies/{pid}/expiry", response_model=ExpiryOut)
def get_expiry(pid: str, horizon_days: int = 60, db: Session = Depends(get_db)):
    return engines.get_expiry(db, pid, horizon_days)


@owner.get("/pharmacies/{pid}/orders", response_model=list[OrderOut])
def list_orders(pid: str, db: Session = Depends(get_db)):
    return engines.list_orders(db, pid)


@owner.get("/pharmacies/{pid}/orders/{oid}/trim", response_model=TrimOut)
def get_trim(pid: str, oid: str, db: Session = Depends(get_db)):
    return engines.get_trim(db, pid, oid)


@owner.post("/pharmacies/{pid}/funding-plan", response_model=FundingPlanOut)
def funding_plan(pid: str, body: FundingRequest | None = Body(default=None), db: Session = Depends(get_db)):
    if body is None or (body.amount is None and body.needed_by is None):
        return engines.get_funding_plan(db, pid)
    default = engines.get_funding_plan(db, pid).need
    need = FundingNeed(amount=default.amount if body.amount is None else body.amount,
                       needed_by=body.needed_by or default.needed_by)
    return engines.get_funding_plan(db, pid, need)


@owner.get("/pharmacies/{pid}/financing-catalogue", response_model=CatalogueOut)
def financing_catalogue(pid: str, db: Session = Depends(get_db)):
    """Sourced Bangladeshi financing archetypes matched to the need: N matched, K eligible,
    cheapest first, with the reason each other option doesn't fit."""
    return catalogue.get_catalogue(db, pid)


@owner.get("/pharmacies/{pid}/passport", response_model=PassportOut)
def get_passport(pid: str, db: Session = Depends(get_db)):
    return engines.get_passport(db, pid)


@owner.get("/pharmacies/{pid}/shelf-life-credit", response_model=ShelfLifeCreditOut)
def get_shelf_life_credit(pid: str, db: Session = Depends(get_db)):
    """What a purpose-blind lender would finance vs what LaMP finances once stock that
    won't sell before expiry is left out."""
    return engines.get_shelf_life_credit(db, pid)


# --- Actions: only this approve endpoint can approve ------------------------------------

@owner.get("/pharmacies/{pid}/actions", response_model=list[ActionOut])
def list_actions(pid: str, db: Session = Depends(get_db)):
    return engines.list_actions(db, pid)


@owner.post("/pharmacies/{pid}/actions", response_model=ActionOut)
def propose_action(pid: str, proposal: ActionProposal, db: Session = Depends(get_db)):
    """Over HTTP the caller is always the owner: `proposed_by` in the body is ignored.
    The chat proposes in-process as "agent", the follow-up runner as "lamp-scheduler"."""
    return engines.propose_action(db, pid, proposal.model_copy(update={"proposed_by": None}), "owner")


@owner.post("/pharmacies/{pid}/actions/{aid}/approve", response_model=ActionOut)
def approve_action(pid: str, aid: str, body: ApprovalIn | None = Body(default=None), db: Session = Depends(get_db)):
    """Loan applications (Tier 3) re-ask the owner PIN: re-authentication at approval."""
    a = action_engine.get_action(db, pid, aid)
    if action_engine.requires_pin(a.kind):
        ph = engines.get_pharmacy(db, pid)
        _refuse_if_locked(ph)
        if not auth.check_pin(db, ph, body.pin if body else None):
            engines.log("T3", "ACTIONS", "approval_pin_rejected", db, action=aid, kind=a.kind)
            db.commit()
            raise HTTPException(401, "This approval needs the owner PIN")
    return action_engine.execute_owner_approval(db, pid, aid)


@owner.post("/pharmacies/{pid}/actions/{aid}/reject", response_model=ActionOut)
def reject_action(pid: str, aid: str, db: Session = Depends(get_db)):
    return engines.reject_action(db, pid, aid)


@owner.get("/pharmacies/{pid}/followups", response_model=list[FollowUpOut])
def list_followups(pid: str, db: Session = Depends(get_db)):
    """The approved plan's conditional steps and whether they have fired."""
    engines.get_pharmacy(db, pid)
    return followups.list_followups(db, pid)


@owner.get("/pharmacies/{pid}/policy", response_model=PolicyOut)
def get_policy(pid: str, db: Session = Depends(get_db)):
    """The rules LaMP enforces: Pause, the PIN at loan approval, and the borrowing ceiling
    with its published source."""
    return policy.get_policy(db, pid)


@owner.get("/pharmacies/{pid}/pause", response_model=PauseOut)
def get_pause(pid: str, db: Session = Depends(get_db)):
    return policy.get_pause(db, pid)


@owner.post("/pharmacies/{pid}/pause", response_model=PauseOut)
def set_pause(pid: str, body: PauseIn, db: Session = Depends(get_db)):
    """Pause LaMP: the copilot and the scheduler can't propose, and their proposals can't
    be approved, until the owner resumes it."""
    return policy.set_pause(db, pid, body.paused)


# --- Consents and lenders ---------------------------------------------------------------

@owner.get("/pharmacies/{pid}/consents", response_model=list[ConsentOut])
def list_consents(pid: str, db: Session = Depends(get_db)):
    return engines.list_consents(db, pid)


@owner.get("/pharmacies/{pid}/consents/preview", response_model=ConsentPreview)
def consent_preview(pid: str, lender_id: str, scopes: str = "passport.summary", db: Session = Depends(get_db)):
    """What this lender would see with these scopes (comma-separated), before sharing."""
    from app.engines.lenders import consent_preview as preview

    return preview(db, pid, lender_id, [s for s in scopes.split(",") if s])


@owner.post("/pharmacies/{pid}/consents", response_model=ConsentOut)
def grant_consent(pid: str, body: ConsentIn, db: Session = Depends(get_db)):
    return engines.grant_consent(db, pid, body)


@owner.delete("/pharmacies/{pid}/consents/{consent_id}")
def revoke_consent(pid: str, consent_id: str, db: Session = Depends(get_db)) -> dict:
    return engines.revoke_consent(db, pid, consent_id)


@router.get("/lenders", response_model=list[LenderOut])
def list_lenders(db: Session = Depends(get_db)):
    return engines.list_lenders(db)


@lender.get("/lenders/{lid}/applications", response_model=list[ApplicationOut])
def lender_inbox(lid: str, db: Session = Depends(get_db)):
    return engines.inbox(db, lid)


@lender.post("/lenders/{lid}/applications/{appid}/decide", response_model=ApplicationOut)
def decide_application(lid: str, appid: str, db: Session = Depends(get_db)):
    return engines.decide(db, lid, appid)


# --- Audit log ----------------------------------------------------------------------------

@logs.get("/logs", response_model=list[LogEvent])
def get_logs(since: str | None = None, db: Session = Depends(get_db)):
    """All events, or those after `since` (a log id like lg-12, or an ISO timestamp)."""
    return logbus.events(db, since)


@logs.get("/logs/export", response_class=PlainTextResponse)
def export_logs(format: Literal["text", "jsonl"] = "text", db: Session = Depends(get_db)) -> str:
    """The audit log, one event per line: readable text (the sandbox execution trace), or
    JSONL with every field and both hashes, which scripts/verify_trace.py can re-check."""
    evs = logbus.events(db)
    if format == "jsonl":
        prevs = [logbus.GENESIS] + [e.hash for e in evs[:-1]]
        return "".join(json.dumps(logbus.as_record(e, p), ensure_ascii=False) + "\n" for e, p in zip(evs, prevs))
    return "\n".join(logbus.as_text(e) for e in evs) + "\n"


@logs.get("/logs/verify", response_model=VerifyOut)
def verify_logs(db: Session = Depends(get_db)):
    """Recompute the hash chain: intact, number of events, and the head hash."""
    return logbus.verify(db)


@logs.get("/logs/stream")
async def stream_logs(once: bool = False, db: Session = Depends(get_db)):
    """Server-Sent Events: every past event, then new ones as they happen.
    `once=true` sends the backlog and closes (for tests). After /dev/reset the log ids restart
    at lg-1, so the stream closes; the browser's EventSource reconnects and gets the new log."""
    factory = sessionmaker(bind=db.get_bind())

    async def gen():
        last = 0
        while True:
            with factory() as s:
                batch = logbus.events(s, after_id=last)
                reset = not batch and last and s.get(m.AuditLog, last) is None
            if reset:
                return
            for e in batch:
                last = int(e.id[3:])
                yield f"id: {e.id}\ndata: {json.dumps(e.model_dump(mode='json'))}\n\n"
            if once:
                return
            yield ": keepalive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


router.include_router(owner, dependencies=[Depends(require_owner)])
router.include_router(lender, dependencies=[Depends(require_lender)])
router.include_router(logs, dependencies=[Depends(require_any_owner)])
router.include_router(dev, dependencies=[Depends(dev_only)])

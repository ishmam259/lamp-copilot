"""REST endpoints (docs/PLAN.md section 4.1).

Pharmacy, captures, accounts, dues, forecast, alerts and orders read the
database through the engines. The rest still return the golden examples from
examples.py, with a small in-memory store for actions, consents and logs,
until F3-F5 replace them.
"""

import asyncio
import copy
import importlib
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import engines
from app.db import models as m
from app.db.seed import apply_extraction, load_seed
from app.db.session import get_db

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
    LenderOut,
    LogEvent,
    OrderOut,
    PassportOut,
    PharmacyOut,
    TrimOut,
)

from . import examples as ex

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class _Store:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.actions = copy.deepcopy(ex.ACTIONS)
        self.consents: list[dict] = []
        self.applications: list[dict] = []
        self.captures: dict[str, dict] = {}
        self.logs = copy.deepcopy(ex.LOGS)

    def log(self, tier: str, component: str, event: str, **data) -> None:
        self.logs.append({"id": f"lg-{len(self.logs) + 1}", "ts": _now(), "tier": tier,
                          "component": component, "event": event, "data": data})


store = _Store()


def _check_pid(pid: str) -> None:
    if pid != ex.PID:
        raise HTTPException(404, f"Unknown pharmacy '{pid}'")


def _find(items: list[dict], key: str, value: str, what: str) -> dict:
    for item in items:
        if item[key] == value:
            return item
    raise HTTPException(404, f"Unknown {what} '{value}'")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/dev/reset")
def dev_reset(with_demo_captures: bool = False, db: Session = Depends(get_db)) -> dict:
    load_seed(db, with_demo_captures=with_demo_captures)
    store.reset()
    store.log("T0", "DEV", "reset", with_demo_captures=with_demo_captures)
    return {"status": "ok", "pharmacy_id": ex.PID, "with_demo_captures": with_demo_captures}


@router.get("/pharmacies/{pid}", response_model=PharmacyOut)
def get_pharmacy(pid: str, db: Session = Depends(get_db)):
    ph = engines.get_pharmacy(db, pid)
    return {"id": ph.id, "name": ph.name, "city": ph.city, "settings": ph.settings}


# --- Captures -------------------------------------------------------------

async def _extract(image: bytes, kind: str) -> dict:
    """Call Pritom's extractor if it exists, else return the example draft."""
    try:
        extraction = importlib.import_module("app.agents.extraction")
        result = await extraction.extract(image, kind)
        return ExtractionResult.model_validate(result).model_dump(mode="json")
    except ImportError:
        return copy.deepcopy(ex.CAPTURE_INVOICE["extraction"])


def _capture_out(cap: m.Capture) -> dict:
    return {"id": cap.id, "kind": cap.kind, "status": cap.status, "image_url": None, "extraction": cap.extraction}


@router.post("/pharmacies/{pid}/captures", response_model=CaptureOut)
async def create_capture(pid: str, file: UploadFile = File(...),
                         kind: Literal["invoice", "sales_page"] = Form(...), db: Session = Depends(get_db)):
    engines.get_pharmacy(db, pid)
    extraction = await _extract(await file.read(), kind)
    n = len(db.scalars(select(m.Capture.id)).all()) + 1
    cap = m.Capture(id=f"cap-{n}", pharmacy_id=pid, kind=kind, status="needs_review",
                    extraction=extraction, created_at=datetime.now(timezone.utc))
    db.add(cap)
    db.commit()
    store.log("T1", "CAPTURE", "capture_created", capture=cap.id, kind=kind,
              suspicious_text=len(extraction.get("suspicious_text", [])))
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
    db.commit()
    store.log("T1", "CAPTURE", "capture_confirmed", capture=cid)
    return _capture_out(cap)


# --- Read views -------------------------------------------------------------

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
def get_expiry(pid: str, horizon_days: int = 60):
    _check_pid(pid)
    return ex.EXPIRY


@router.get("/pharmacies/{pid}/orders", response_model=list[OrderOut])
def list_orders(pid: str, db: Session = Depends(get_db)):
    return engines.list_orders(db, pid)


@router.get("/pharmacies/{pid}/orders/{oid}/trim", response_model=TrimOut)
def get_trim(pid: str, oid: str):
    _check_pid(pid)
    _find(ex.ORDERS, "id", oid, "order")
    return ex.TRIM


@router.post("/pharmacies/{pid}/funding-plan", response_model=FundingPlanOut)
def funding_plan(pid: str, need: FundingNeed | None = Body(default=None)):
    _check_pid(pid)
    return ex.FUNDING_PLAN


@router.get("/pharmacies/{pid}/passport", response_model=PassportOut)
def get_passport(pid: str):
    _check_pid(pid)
    return ex.PASSPORT


# --- Actions (only the approve endpoint can approve) -------------------------

@router.get("/pharmacies/{pid}/actions", response_model=list[ActionOut])
def list_actions(pid: str):
    _check_pid(pid)
    return store.actions


@router.post("/pharmacies/{pid}/actions", response_model=ActionOut)
def propose_action(pid: str, proposal: ActionProposal, proposed_by: Literal["owner", "agent"] = "owner"):
    _check_pid(pid)
    action = {"id": f"act-{len(store.actions) + 1}", "kind": proposal.kind, "status": "proposed",
              "payload": proposal.payload, "proposed_by": proposed_by, "created_at": _now(),
              "decided_at": None, "result": None}
    store.actions.append(action)
    store.log("T1", "ACTIONS", "action_proposed", action=action["id"], kind=proposal.kind, by=proposed_by)
    return action


_STUB_RESULTS = {
    "return_claim": {"claim_id": "CLM-0001", "expected_credit": 9200},
    "extension_request": {"status": "awaiting_supplier"},
    "trim_order": {"order_id": "o-1", "new_total": 49200},
    "set_aside": {"status": "scheduled"},
    "loan_application": {"application_id": "APP-0001"},
}


@router.post("/pharmacies/{pid}/actions/{aid}/approve", response_model=ActionOut)
def approve_action(pid: str, aid: str):
    _check_pid(pid)
    action = _find(store.actions, "id", aid, "action")
    if action["status"] != "proposed":
        raise HTTPException(409, f"Action is already {action['status']}")
    action.update(status="executed", decided_at=_now(), result=_STUB_RESULTS[action["kind"]])
    store.log("T3" if action["kind"] == "loan_application" else "T2", "EXECUTOR", "action_executed",
              action=aid, kind=action["kind"])
    return action


@router.post("/pharmacies/{pid}/actions/{aid}/reject", response_model=ActionOut)
def reject_action(pid: str, aid: str):
    _check_pid(pid)
    action = _find(store.actions, "id", aid, "action")
    if action["status"] != "proposed":
        raise HTTPException(409, f"Action is already {action['status']}")
    action.update(status="rejected", decided_at=_now())
    store.log("T1", "ACTIONS", "action_rejected", action=aid)
    return action


# --- Consents and lenders -----------------------------------------------------

@router.get("/pharmacies/{pid}/consents", response_model=list[ConsentOut])
def list_consents(pid: str):
    _check_pid(pid)
    return store.consents


@router.post("/pharmacies/{pid}/consents", response_model=ConsentOut)
def grant_consent(pid: str, body: ConsentIn):
    _check_pid(pid)
    _find(ex.LENDERS, "id", body.lender_id, "lender")
    consent = {"id": f"cons-{len(store.consents) + 1}", "lender_id": body.lender_id,
               "scopes": body.scopes, "granted_at": _now()}
    store.consents.append(consent)
    store.log("T1", "CONSENT", "consent_granted", consent=consent["id"], lender=body.lender_id)
    return consent


@router.delete("/pharmacies/{pid}/consents/{consent_id}")
def revoke_consent(pid: str, consent_id: str) -> dict:
    _check_pid(pid)
    consent = _find(store.consents, "id", consent_id, "consent")
    store.consents.remove(consent)
    store.log("T1", "CONSENT", "consent_revoked", consent=consent_id)
    return {"status": "revoked", "id": consent_id}


@router.get("/lenders", response_model=list[LenderOut])
def list_lenders():
    return ex.LENDERS


@router.get("/lenders/{lid}/applications", response_model=list[ApplicationOut])
def lender_inbox(lid: str):
    _find(ex.LENDERS, "id", lid, "lender")
    consented = any(c["lender_id"] == lid for c in store.consents)
    store.log("T0", "LENDER", "inbox_viewed", lender=lid)
    return [a for a in store.applications if a["lender_id"] == lid] if consented else []


@router.post("/lenders/{lid}/applications/{appid}/decide", response_model=ApplicationOut)
def decide_application(lid: str, appid: str):
    app_ = _find(store.applications, "id", appid, "application")
    if app_["lender_id"] != lid:
        raise HTTPException(404, f"Unknown application '{appid}'")
    app_.update(status="approved", decision=ex.APPLICATION_DECIDED["decision"])
    store.log("T3", "LENDER", "application_decided", application=appid, approved=True)
    return app_


# --- Audit log ------------------------------------------------------------------

@router.get("/logs", response_model=list[LogEvent])
def get_logs(since: str | None = None):
    return [e for e in store.logs if since is None or e["ts"] > since]


@router.get("/logs/stream")
async def stream_logs():
    async def events():
        sent = 0
        while True:
            while sent < len(store.logs):
                yield f"data: {json.dumps(store.logs[sent])}\n\n"
                sent += 1
            yield ": keepalive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(events(), media_type="text/event-stream")

"""The closed API (win plan CORE-13): the 10 direct-HTTP cases, plus the PIN and the session."""

import pytest

from app.config import settings
from api_support import PIN, lender_headers

P = "/api/v1/pharmacies/green-life"
W = "/api/v1/lenders/wallet-lender"


def _loan_proposal(client):
    """A loan application proposed by the signed-in owner (consent given first)."""
    client.post(f"{P}/consents", json={"lender_id": "wallet-lender"})
    r = client.post(f"{P}/actions", json={"kind": "loan_application", "payload": {
        "lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": 8200}})
    assert r.status_code == 200, r.text
    return r.json()


# --- The 10 direct-HTTP cases ---------------------------------------------------------------

def test_01_passport_without_session_is_401(anon):
    assert anon.get(f"{P}/passport").status_code == 401


def test_02_lender_key_on_owner_read_is_403(anon):
    assert anon.get(f"{P}/passport", headers=lender_headers()).status_code == 403


def test_03_chat_without_session_is_401(anon):
    r = anon.post("/api/v1/chat", json={"trigger": "submit-message", "id": "c1", "messages": []})
    assert r.status_code == 401


def test_04_log_stream_without_session_is_401(anon):
    assert anon.get("/api/v1/logs/stream?once=true").status_code == 401
    assert anon.get("/api/v1/logs").status_code == 401
    assert anon.get("/api/v1/logs/export").status_code == 401


def test_05_approve_without_session_is_401(client, anon):
    a = client.post(f"{P}/actions", json={"kind": "set_aside", "payload": {"amount": 500}}).json()
    anon.cookies.clear()
    assert anon.post(f"{P}/actions/{a['id']}/approve", json={"pin": PIN}).status_code == 401


def test_06_approve_with_lender_key_is_403(client):
    a = client.post(f"{P}/actions", json={"kind": "set_aside", "payload": {"amount": 500}}).json()
    client.cookies.clear()
    r = client.post(f"{P}/actions/{a['id']}/approve", json={"pin": PIN}, headers=lender_headers())
    assert r.status_code == 403


def test_07_consent_without_session_is_401(anon):
    assert anon.post(f"{P}/consents", json={"lender_id": "wallet-lender"}).status_code == 401


def test_08_lender_decide_without_key_is_401(client):
    assert client.post(f"{W}/applications/APP-0001/decide").status_code == 401
    assert client.get(f"{W}/applications").status_code == 401
    # another lender's key doesn't open this lender's inbox
    assert client.get(f"{W}/applications", headers=lender_headers("partner-bank")).status_code == 403


def test_09_dev_reset_without_dev_mode_is_404(client, monkeypatch):
    monkeypatch.setattr(settings, "dev_mode", False)
    assert client.post("/api/v1/dev/reset").status_code == 404
    assert client.post("/api/v1/dev/simulate/supplier-reply", json={"action_id": "x", "accepted": True}).status_code == 404


def test_10_spoofed_proposed_by_is_recorded_as_the_caller(client):
    r = client.post(f"{P}/actions?proposed_by=agent",
                    json={"kind": "set_aside", "payload": {}, "proposed_by": "agent"})
    assert r.json()["proposed_by"] == "owner"
    ev = [e for e in client.get("/api/v1/logs").json() if e["event"] == "action_proposed"][-1]
    assert ev["data"]["by"] == "owner"


# --- PIN, session and approval ---------------------------------------------------------------

def test_wrong_pin_is_401_and_logged(anon):
    assert anon.post(f"{P}/session", json={"pin": "0000"}).status_code == 401
    assert anon.get(f"{P}/accounts").status_code == 401
    assert anon.post(f"{P}/session", json={"pin": PIN}).status_code == 200
    assert "unlock_failed" in [e["event"] for e in anon.get("/api/v1/logs").json()]


def test_session_cookie_is_httponly(anon):
    r = anon.post(f"{P}/session", json={"pin": PIN})
    assert r.json()["role"] == "owner"
    assert "httponly" in r.headers["set-cookie"].lower()


def test_loan_approval_needs_the_pin_again(client):
    a = _loan_proposal(client)
    assert a["requires_pin"] is True
    assert client.post(f"{P}/actions/{a['id']}/approve").status_code == 401
    assert client.post(f"{P}/actions/{a['id']}/approve", json={"pin": "1111"}).status_code == 401
    assert client.post(f"{P}/actions/{a['id']}/approve", json={"pin": PIN}).json()["status"] == "executed"
    assert "approval_pin_rejected" in [e["event"] for e in client.get("/api/v1/logs").json()]


def test_other_actions_dont_need_the_pin(client):
    a = client.post(f"{P}/actions", json={"kind": "set_aside", "payload": {"amount": 500}}).json()
    assert a["requires_pin"] is False
    assert client.post(f"{P}/actions/{a['id']}/approve").json()["status"] == "executed"


def test_pin_hash_is_not_exposed(client):
    assert "owner_pin" not in client.get(P).json()["settings"]


def test_reset_keeps_the_owner_signed_in(client):
    assert client.post("/api/v1/dev/reset").status_code == 200
    assert client.get(f"{P}/accounts").status_code == 200


# --- Pause (CORE-08) -------------------------------------------------------------------------

def test_pause_blocks_the_copilot_but_not_the_owner(client, api_db):
    from fastapi import HTTPException

    from app.engines import actions as action_engine
    from app.schemas import ActionProposal

    # the copilot proposes before the pause (in-process, as the chat does)
    early = action_engine.propose_action(api_db, "green-life", ActionProposal(kind="set_aside", payload={}), "agent")
    api_db.commit()
    assert client.post(f"{P}/pause", json={"paused": True}).json()["paused"] is True
    assert client.get(f"{P}/pause").json()["paused"] is True
    api_db.expire_all()
    with pytest.raises(HTTPException) as e:
        action_engine.propose_action(api_db, "green-life", ActionProposal(kind="set_aside", payload={}), "agent")
    assert e.value.status_code == 409
    assert client.post(f"{P}/actions/{early.id}/approve").status_code == 409
    owner_own = client.post(f"{P}/actions", json={"kind": "set_aside", "payload": {}}).json()
    assert client.post(f"{P}/actions/{owner_own['id']}/approve").json()["status"] == "executed"
    events = [e["event"] for e in client.get("/api/v1/logs").json()]
    assert {"agent_paused", "proposal_refused_paused", "approval_refused_paused"} <= set(events)
    client.post(f"{P}/pause", json={"paused": False})
    assert client.post(f"{P}/actions/{early.id}/approve").json()["status"] == "executed"


def test_five_wrong_pins_lock_the_unlock(anon):
    for _ in range(5):
        assert anon.post(f"{P}/session", json={"pin": "0000"}).status_code == 401
    r = anon.post(f"{P}/session", json={"pin": PIN})  # even the right PIN waits out the lockout
    assert r.status_code == 429 and r.json()["detail"] == "Too many wrong PINs. Try again in 15 minutes."


def test_a_right_pin_resets_the_count(anon):
    for _ in range(4):
        anon.post(f"{P}/session", json={"pin": "0000"})
    assert anon.post(f"{P}/session", json={"pin": PIN}).status_code == 200
    for _ in range(4):
        assert anon.post(f"{P}/session", json={"pin": "0000"}).status_code == 401
    assert anon.post(f"{P}/session", json={"pin": PIN}).status_code == 200


def test_lock_ends_the_session(client):
    assert client.delete(f"{P}/session").status_code == 204
    assert client.get(f"{P}/passport").status_code == 401
    assert client.delete(f"{P}/session").status_code == 204  # already locked: still fine


def test_reset_can_default_to_the_demo_captures(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_reset_with_captures", True)
    assert client.post("/api/v1/dev/reset").json()["with_demo_captures"] is True
    assert client.post("/api/v1/dev/reset?with_demo_captures=false").json()["with_demo_captures"] is False

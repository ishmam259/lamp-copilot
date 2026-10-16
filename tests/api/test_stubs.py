"""M1 contract smoke tests: every stub endpoint answers with a valid, golden shape."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
P = "/api/v1/pharmacies/green-life"


@pytest.fixture(autouse=True)
def reset():
    client.post("/api/v1/dev/reset")


@pytest.mark.parametrize("path", [
    "/api/v1/health", P, f"{P}/accounts", f"{P}/dues", f"{P}/forecast", f"{P}/alerts",
    f"{P}/expiry", f"{P}/orders", f"{P}/orders/o-1/trim", f"{P}/passport", f"{P}/actions",
    f"{P}/consents", "/api/v1/lenders", "/api/v1/logs", f"{P}/captures/cap-demo",
])
def test_get_endpoints(path):
    assert client.get(path).status_code == 200


def test_golden_numbers_in_examples():
    acc = client.get(f"{P}/accounts").json()
    assert (acc["sales"], acc["net_profit"], acc["stock_days"], acc["patient_due_days"]) == (412500, 13500, 17.4, 2.8)
    fc = client.get(f"{P}/forecast").json()
    assert fc["days"][9]["balance"] == 41000
    assert fc["shortfalls"][0] == {"date": "2026-10-26", "amount": 19000, "cause": "Supplier A order BDT 60,000"}
    trim = client.get(f"{P}/orders/o-1/trim").json()
    assert (trim["suggested_total"], trim["saving"]) == (49200, 10800)
    plan = client.post(f"{P}/funding-plan").json()
    assert plan["need"]["amount"] == 8200 and plan["naive_cost_bdt"] == 421.64
    costs = {o["key"]: o["cost_bdt"] for o in plan["options"]}
    assert costs["wallet_loan"] == 181.97 and costs["bank_supplier_credit"] == 492
    pp = client.get(f"{P}/passport").json()
    assert (pp["theta_low_5pct"], pp["default_probability"], pp["score"]) == (0.826, 0.03, 0.507)
    assert sum(e["on_time"] for e in pp["evidence"]) == 38


def test_action_flow():
    act = client.post(f"{P}/actions", json={"kind": "extension_request", "payload": {"amount": 8200}}).json()
    assert act["status"] == "proposed"
    done = client.post(f"{P}/actions/{act['id']}/approve").json()
    assert done["status"] == "executed" and done["result"] == {"status": "awaiting_supplier"}
    assert client.post(f"{P}/actions/{act['id']}/approve").status_code == 409


def test_capture_upload_falls_back_to_example():
    r = client.post(f"{P}/captures", files={"file": ("inv.jpg", b"fake", "image/jpeg")}, data={"kind": "invoice"})
    assert r.status_code == 200 and r.json()["status"] == "needs_review"
    cid = r.json()["id"]
    assert client.post(f"{P}/captures/{cid}/confirm", json={}).json()["status"] == "confirmed"


def test_unknown_pharmacy():
    assert client.get("/api/v1/pharmacies/nope/accounts").status_code == 404

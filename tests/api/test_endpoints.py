"""API round trips: every endpoint answers with a valid shape and the golden numbers."""

import pytest

P = "/api/v1/pharmacies/green-life"


@pytest.mark.parametrize("path", [
    "/api/v1/health", P, f"{P}/accounts", f"{P}/dues", f"{P}/forecast", f"{P}/alerts",
    f"{P}/expiry", f"{P}/orders", f"{P}/orders/o-1/trim", f"{P}/passport", f"{P}/actions",
    f"{P}/consents", "/api/v1/lenders", "/api/v1/logs", f"{P}/captures/cap-demo",
])
def test_get_endpoints(client, path):
    assert client.get(path).status_code == 200


def test_golden_numbers(client):
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


def test_action_flow(client):
    act = client.post(f"{P}/actions", json={"kind": "extension_request", "payload": {"amount": 8200}}).json()
    assert act["status"] == "proposed"
    done = client.post(f"{P}/actions/{act['id']}/approve").json()
    assert done["status"] == "executed" and done["result"]["status"] == "awaiting_supplier"
    assert client.post(f"{P}/actions/{act['id']}/approve").status_code == 409


def test_capture_confirm_saves_invoice_and_stock(client):
    r = client.post(f"{P}/captures", files={"file": ("inv.jpg", b"fake", "image/jpeg")}, data={"kind": "invoice"})
    assert r.status_code == 200 and r.json()["status"] == "needs_review"
    cid = r.json()["id"]
    stock_before = client.get(f"{P}/accounts").json()["stock_value"]
    assert client.post(f"{P}/captures/{cid}/confirm", json={}).json()["status"] == "confirmed"
    assert client.get(f"{P}/accounts").json()["stock_value"] == stock_before + 7350  # sample draft's lines
    assert "K-77310" in [i["invoice_no"] for i in client.get(f"{P}/dues").json()["items"]]
    assert client.post(f"{P}/captures/{cid}/confirm", json={}).status_code == 409


def test_reset_without_captures(client):
    assert client.post("/api/v1/dev/reset").status_code == 200
    assert client.get(f"{P}/accounts").json()["stock_value"] == 192500


def test_unknown_pharmacy(client):
    # A signed-in owner can't reach another pharmacy's data.
    assert client.get("/api/v1/pharmacies/nope/accounts").status_code == 403


@pytest.mark.parametrize("body", [None, {}, {"amount": None}])
def test_funding_plan_empty_body_is_default(client, body):
    r = client.post(f"{P}/funding-plan", json=body) if body is not None else client.post(f"{P}/funding-plan")
    assert r.status_code == 200 and r.json()["need"] == {"amount": 8200, "needed_by": "2026-10-26"}


def test_funding_plan_partial_body(client):
    assert client.post(f"{P}/funding-plan", json={"amount": 5000}).json()["need"] == {"amount": 5000, "needed_by": "2026-10-26"}
    assert client.post(f"{P}/funding-plan", json={"needed_by": "2026-10-20"}).json()["need"] == {"amount": 8200, "needed_by": "2026-10-20"}
    assert client.post(f"{P}/funding-plan", json={"amount": "lots"}).status_code == 422


def test_sales_page_capture_saves_only_sales_days(client):
    r = client.post(f"{P}/captures", files={"file": ("p.jpg", b"x", "image/jpeg")}, data={"kind": "sales_page"})
    assert r.json()["extraction"]["kind"] == "sales_page" and r.json()["extraction"]["invoice"] is None
    client.post(f"{P}/captures/{r.json()['id']}/confirm", json={})
    assert "K-77310" not in [i["invoice_no"] for i in client.get(f"{P}/dues").json()["items"]]
    assert client.get(f"{P}/accounts").json()["sales"] == 412500  # same days re-entered, same totals


def test_shelf_life_credit_endpoint(client):
    s = client.get(f"{P}/shelf-life-credit").json()
    assert (s["counterfactual_purpose_blind"], s["not_financed"], s["financeable"]) == (19000, 10800, 8200)

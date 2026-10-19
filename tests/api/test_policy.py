"""Borrowing ceiling (win plan CORE-07): debt burden ratio capped at 35% of monthly net cash
flow, following Bangladesh Bank's published DBR limit for unsecured personal loans."""

from app.config import REPO_ROOT

P = "/api/v1/pharmacies/green-life"


def _loan(client, amount):
    return client.post(f"{P}/actions", json={"kind": "loan_application", "payload": {
        "lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": amount}})


def test_the_plans_loan_is_within_the_ceiling(client):
    r = _loan(client, 8200)
    assert r.status_code == 200 and r.json()["status"] == "proposed"


def test_a_loan_for_the_untrimmed_shortfall_is_refused(client):
    r = _loan(client, 19000)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "6,473.88" in detail and "48.0%" in detail and "35% cap" in detail and "Bangladesh Bank" in detail
    assert "loan_refused_dbr" in [e["event"] for e in client.get("/api/v1/logs").json()]
    assert [a for a in client.get(f"{P}/actions").json() if a["kind"] == "loan_application"] == []


def test_the_copilot_is_held_to_the_same_ceiling(client, api_db):
    import pytest
    from fastapi import HTTPException

    from app.engines import actions as action_engine
    from app.schemas import ActionProposal

    with pytest.raises(HTTPException) as e:
        action_engine.propose_action(api_db, "green-life", ActionProposal(kind="loan_application", payload={
            "lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": 19000}), "agent")
    assert e.value.status_code == 409


def test_policy_endpoint_shows_the_rule_and_its_source(client):
    p = client.get(f"{P}/policy").json()
    assert (p["dbr_cap_pct"], p["monthly_net_cash_flow"], p["pin_required_for"]) == (35.0, 13500, ["loan_application"])
    assert p["source"]["page"] == 65 and "No. 12" in p["source"]["clause"]
    assert (REPO_ROOT / p["source"]["file"]).exists()
    plan, naive = p["examples"]
    assert (plan["amount"], plan["monthly_repayment"], plan["dbr_pct"], plan["ok"]) == (8200, 2793.99, 20.7, True)
    assert (naive["amount"], naive["monthly_repayment"], naive["dbr_pct"], naive["ok"]) == (19000, 6473.88, 48.0, False)


def test_out_of_limit_amounts_are_left_to_the_executor(client):
    # 50,000 is above the wallet loan's limit: proposed, then fails at execution as before
    assert _loan(client, 50000).status_code == 200


def test_credit_and_examples_keep_the_pre_trim_order_after_the_trim(client):
    trim = client.post(f"{P}/actions", json={"kind": "trim_order", "payload": {}}).json()
    assert client.post(f"{P}/actions/{trim['id']}/approve", json={}).json()["status"] == "executed"
    c = client.get(f"{P}/shelf-life-credit").json()
    assert (c["counterfactual_purpose_blind"], c["not_financed"], c["financeable"]) == (19000, 10800, 8200)
    plan, naive = client.get(f"{P}/policy").json()["examples"]
    assert (plan["amount"], plan["ok"], naive["amount"], naive["dbr_pct"], naive["ok"]) == (8200, True, 19000, 48.0, False)

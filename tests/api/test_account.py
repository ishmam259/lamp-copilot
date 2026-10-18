"""Sandbox wallet and reconciliation (win plan CORE-05)."""

from api_support import PIN, lender_headers

P = "/api/v1/pharmacies/green-life"


def test_reconciliation_finds_exactly_the_planted_problems(client):
    a = client.get(f"{P}/account").json()
    assert a["counts"] == {"matched": 11, "duplicate": 1, "unmatched": 1, "missing_from_statement": 1}
    by = {s: [x for x in a["matches"] if x["status"] == s] for s in a["counts"]}
    assert [(x["invoice_no"], x["amount"]) for x in by["duplicate"]] == [("Q-3130", -8600)]
    assert [x["payee"] for x in by["unmatched"]] == ["MERCHANT 01712XXXXXX"]
    assert [x["invoice_no"] for x in by["missing_from_statement"]] == ["T-3134"]
    assert len(a["recommendations"]) == 3 and "8,600" in a["recommendations"][0]


def test_loan_payout_lands_in_the_wallet(client):
    before = client.get(f"{P}/account").json()
    assert before["transactions"] == [] and before["opening_balance"] == before["balance"]
    client.post(f"{P}/consents", json={"lender_id": "wallet-lender"})
    loan = client.post(f"{P}/actions", json={"kind": "loan_application", "payload": {
        "lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": 8200}}).json()
    app_id = client.post(f"{P}/actions/{loan['id']}/approve", json={"pin": PIN}).json()["result"]["application_id"]
    d = client.post(f"/api/v1/lenders/wallet-lender/applications/{app_id}/decide", headers=lender_headers()).json()
    after = client.get(f"{P}/account").json()
    assert after["balance"] == before["balance"] + 8200 and after["opening_balance"] == before["opening_balance"]
    [t] = after["transactions"]
    assert (t["amount"], t["kind"], t["ref"]) == (8200, "loan_payout", d["decision"]["payout_ref"])
    assert after["counts"]["matched"] == 12
    assert "wallet_credited" in [e["event"] for e in client.get("/api/v1/logs").json()]

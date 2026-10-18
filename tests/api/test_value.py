"""Value ledger (win plan CORE-10), after the demo story's approvals."""

from api_support import PIN

P = "/api/v1/pharmacies/green-life"


def _approve(client, kind, **payload):
    a = client.post(f"{P}/actions", json={"kind": kind, "payload": payload}).json()
    return client.post(f"{P}/actions/{a['id']}/approve", json={"pin": PIN}).json()


def test_empty_before_any_action(client):
    assert client.get(f"{P}/value").json() == {"items": [], "total": 0}


def test_demo_story_value(client):
    _approve(client, "return_claim")
    _approve(client, "trim_order", order_id="o-1")
    client.post(f"{P}/consents", json={"lender_id": "wallet-lender"})
    _approve(client, "loan_application", lender_id="wallet-lender", product_key="wallet_loan", amount=8200)
    v = client.get(f"{P}/value").json()
    assert [(i["kind"], i["amount"]) for i in v["items"]] == [
        ("return_claim", 9200), ("trim_order", 10800), ("interest_avoided", 239.67)]
    assert v["total"] == 20239.67
    assert all(i["basis"] and i["counterfactual"] for i in v["items"])


def test_accepted_extension_counts_the_avoided_loan(client):
    ext = _approve(client, "extension_request", amount=8200)
    client.post("/api/v1/dev/simulate/supplier-reply", json={"action_id": ext["id"], "outcome": "accepted"})
    [i] = client.get(f"{P}/value").json()["items"]
    assert (i["kind"], i["amount"]) == ("interest_avoided", 181.97)

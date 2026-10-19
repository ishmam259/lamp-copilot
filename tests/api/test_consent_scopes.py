"""Consent scopes enforced for lenders (win plan CORE-16)."""

from api_support import PIN, lender_headers

P = "/api/v1/pharmacies/green-life"
W = "/api/v1/lenders/wallet-lender"


def _apply(client, scopes):
    assert client.post(f"{P}/consents", json={"lender_id": "wallet-lender", "scopes": scopes}).status_code == 200
    loan = client.post(f"{P}/actions", json={"kind": "loan_application", "payload": {
        "lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": 8200}}).json()
    assert client.post(f"{P}/actions/{loan['id']}/approve", json={"pin": PIN}).json()["status"] == "executed"
    [app] = client.get(f"{W}/applications", headers=lender_headers()).json()
    return app["passport"]


def test_summary_only_hides_the_invoice_evidence(client):
    p = _apply(client, ["passport.summary"])
    assert p["score"] == 0.507 and p["paid_on_time"] == 38
    assert p["evidence"] == []


def test_evidence_scope_shows_the_record(client):
    p = _apply(client, ["passport.summary", "passport.evidence"])
    assert len(p["evidence"]) == 41


def test_older_all_in_scope_still_shows_everything(client):
    assert len(_apply(client, ["passport", "accounts"])["evidence"]) == 41


def test_unknown_scope_is_refused(client):
    r = client.post(f"{P}/consents", json={"lender_id": "wallet-lender", "scopes": ["bank_statements"]})
    assert r.status_code == 422


def test_preview_shows_what_the_lender_would_see(client):
    pv = client.get(f"{P}/consents/preview?lender_id=wallet-lender&scopes=passport.summary").json()
    assert pv["passport"]["evidence"] == [] and len(pv["shares"]) == 1 and len(pv["withholds"]) == 1
    full = client.get(f"{P}/consents/preview?lender_id=wallet-lender&scopes=passport.summary,passport.evidence").json()
    assert len(full["passport"]["evidence"]) == 41 and full["withholds"] == []
    assert client.get(f"{P}/consents").json() == []  # a preview shares nothing


def test_withdrawn_consent_keeps_the_row_but_hides_the_passport(client):
    _apply(client, ["passport.summary", "passport.evidence"])
    [c] = client.get(f"{P}/consents").json()
    assert client.delete(f"{P}/consents/{c['id']}").status_code == 200
    [app] = client.get(f"{W}/applications", headers=lender_headers()).json()
    assert (app["status"], app["consent"], app["amount"], app["passport"]) == ("pending", "withdrawn", 8200, None)
    assert client.post(f"{W}/applications/{app['id']}/decide", headers=lender_headers()).status_code == 403

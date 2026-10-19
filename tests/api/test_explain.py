""""Explain this number" rows (P3 / SHOULD-7): the start and +/- rows add up to the = row,
which equals the figure on the screen."""

P = "/api/v1/pharmacies/green-life"


def _adds_up(rows):
    total = 0.0
    for r in rows[:-1]:
        total += -r["amount"] if r["op"] == "-" else r["amount"]
    assert rows[-1]["op"] == "=" and abs(total - rows[-1]["amount"]) < 0.01, rows
    return rows[-1]["amount"]


def test_funding_to_cover_figure_is_explained(client):
    need = client.post(f"{P}/funding-plan", json={}).json()["need"]
    assert _adds_up(need["explain"]) == need["amount"] == 8200


def test_shelf_life_card_is_explained_before_and_after_the_trim(client):
    c = client.get(f"{P}/shelf-life-credit").json()
    assert [r["amount"] for r in c["explain"]] == [19000, 10800, 8200] and _adds_up(c["explain"]) == 8200
    trim = client.post(f"{P}/actions", json={"kind": "trim_order", "payload": {}}).json()
    client.post(f"{P}/actions/{trim['id']}/approve", json={})
    assert _adds_up(client.get(f"{P}/shelf-life-credit").json()["explain"]) == 8200


def test_an_asked_amount_explains_itself(client):
    need = client.post(f"{P}/funding-plan", json={"amount": 5000, "needed_by": "2026-11-01"}).json()["need"]
    assert need["explain"] == [{"label": "Amount to cover", "amount": 5000, "op": "="}]

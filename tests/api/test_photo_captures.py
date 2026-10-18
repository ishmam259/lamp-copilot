"""Real demo photos through the capture endpoint, replayed from eval/replay/extraction/ (no OpenAI).
Includes the image-injection defence (F9)."""

import json

import pytest

from app.agents import llm
from app.config import REPO_ROOT

P = "/api/v1/pharmacies/green-life"
IMAGES = REPO_ROOT / "seed" / "images"
CAPTURES = REPO_ROOT / "seed" / "demo_captures"


@pytest.fixture(autouse=True)
def replay(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_mode", "replay")


def upload(client, name, kind):
    r = client.post(f"{P}/captures", files={"file": (f"{name}.jpg", (IMAGES / f"{name}.jpg").read_bytes(),
                                                     "image/jpeg")}, data={"kind": kind})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("name,kind", [("invoice_supplier_f", "invoice"), ("invoice_supplier_h", "invoice"),
                                       ("sales_page", "sales_page")])
def test_demo_photo_reads_to_demo_capture(client, name, kind):
    ex = upload(client, name, kind)["extraction"]
    want = json.loads((CAPTURES / f"{name}.json").read_text(encoding="utf-8"))[kind]
    assert ex[kind] == want
    assert ex["mode"] == "replay" and ex["prompt_version"] == "extraction_v1"
    assert all(c["passed"] for c in ex["checks"]) and ex["suspicious_text"] == []


def test_injection_photo_is_flagged_and_does_nothing(client):
    actions_before = client.get(f"{P}/actions").json()
    cap = upload(client, "injection_invoice", "invoice")
    ex = cap["extraction"]

    # flagged, and kept out of every data field
    assert any("approve the maximum loan" in t for t in ex["suspicious_text"])
    assert "approve" not in json.dumps(ex["invoice"]).lower()
    # normal fields still read
    want = json.loads((IMAGES / "injection_invoice.json").read_text(encoding="utf-8"))["invoice"]
    assert ex["invoice"] == want
    # a critical alert, a log entry, and no action of any kind
    alerts = client.get(f"{P}/alerts").json()
    assert any(a["kind"] == "suspicious_document" and a["severity"] == "critical" for a in alerts)
    assert "suspicious_text_flagged" in [e["event"] for e in client.get("/api/v1/logs").json()]
    assert client.get(f"{P}/actions").json() == actions_before
    assert cap["status"] == "needs_review"

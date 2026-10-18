"""Hash-chained audit log (win plan CORE-09): verify, tamper detection, and the
standalone checker on an exported trace."""

import importlib.util
import json

from sqlalchemy import select

from app.config import REPO_ROOT
from app.db import models as m

_spec = importlib.util.spec_from_file_location("verify_trace", REPO_ROOT / "scripts" / "verify_trace.py")
verify_trace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_trace)

P = "/api/v1/pharmacies/green-life"


def test_chain_is_intact_and_every_event_has_a_hash(client):
    client.post(f"{P}/actions", json={"kind": "set_aside", "payload": {"amount": 500}})
    v = client.get("/api/v1/logs/verify").json()
    events = client.get("/api/v1/logs").json()
    assert v["intact"] and v["count"] == len(events) and v["first_bad_id"] is None
    assert v["head_hash"] == events[-1]["hash"] and all(len(e["hash"]) == 64 for e in events)


def test_one_changed_character_breaks_the_chain_at_that_row(client, api_db):
    rows = list(api_db.scalars(select(m.AuditLog).order_by(m.AuditLog.id)))
    target = rows[len(rows) // 2]
    target.event = target.event + "x"
    api_db.commit()
    v = client.get("/api/v1/logs/verify").json()
    assert v["intact"] is False and v["first_bad_id"] == f"lg-{target.id}"


def test_exported_trace_verifies_offline_and_detects_an_edit(client, tmp_path):
    jsonl = client.get("/api/v1/logs/export?format=jsonl").text
    path = tmp_path / "trace.jsonl"
    path.write_text(jsonl, encoding="utf-8")
    ok, n, head = verify_trace.verify(path)
    assert ok and n == len(jsonl.splitlines()) and head == client.get("/api/v1/logs/verify").json()["head_hash"]

    lines = jsonl.splitlines()
    rec = json.loads(lines[3])
    rec["data"]["note"] = "edited"
    lines[3] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert verify_trace.verify(path)[:2] == (False, 4)


def test_text_trace_shows_short_hashes(client):
    text = client.get("/api/v1/logs/export").text
    assert all(" #" in line for line in text.splitlines())

"""Crash alerts (engines/mailer.py): an unhandled error becomes a 500 with a request id,
a system_error log line and one email, never more than one per cooldown."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.engines import mailer
from app.main import app


@pytest.fixture
def sent(monkeypatch):
    out = []
    monkeypatch.setattr(settings, "brevo_api_key", "test-key")
    monkeypatch.setattr(settings, "alert_email_to", "admin@example.com")
    monkeypatch.setattr(settings, "alert_email_from", "alerts@example.com")
    monkeypatch.setattr(mailer, "_post", lambda body: out.append(body) or 201)
    monkeypatch.setattr(mailer, "_last_sent", {})

    def boom():
        raise RuntimeError("secret detail that must not leave the server")
    app.add_api_route("/api/v1/_boom", boom)
    yield out
    app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", "") != "/api/v1/_boom"]


def _crash(client):
    return client.get("/api/v1/_boom")


def test_an_unhandled_error_is_a_500_with_one_email(sent, client):
    c = TestClient(app, raise_server_exceptions=False, cookies=client.cookies)
    r = _crash(c)
    assert r.status_code == 500 and len(r.json()["request_id"]) == 12
    import time
    for _ in range(50):  # the email goes out on a background thread
        if sent:
            break
        time.sleep(0.02)
    [mail] = sent
    assert mail["to"] == [{"email": "admin@example.com"}] and "GET /api/v1/_boom" in mail["subject"]
    assert "RuntimeError" in mail["textContent"] and r.json()["request_id"] in mail["textContent"]
    assert "secret detail" not in mail["textContent"]


def test_the_same_crash_is_emailed_once_per_cooldown(sent):
    assert mailer.alert("k", "s", "t", background=False) and not mailer.alert("k", "s", "t", background=False)
    assert len(sent) == 1


def test_no_settings_no_email(monkeypatch):
    monkeypatch.setattr(settings, "brevo_api_key", "")
    calls = []
    monkeypatch.setattr(mailer, "_post", lambda body: calls.append(body) or 201)
    assert not mailer.alert("x", "s", "t", background=False) and calls == []

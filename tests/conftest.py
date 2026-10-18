"""Shared test setup.

Tests run with DEV_MODE on (demo controls and the dev registry key); the test for
DEV_MODE off switches it off itself.

Chat tests (tests/agents/) build their own TestClient without signing in. Until their
fixture logs in with the owner PIN, the owner checks are lifted for those tests only,
so they keep testing the chat. Reminder for the chat owner: log in in
tests/agents/conftest.py (POST /api/v1/pharmacies/green-life/session {"pin": "2468"})
and delete the override below.
"""

import os

os.environ.setdefault("DEV_MODE", "true")

import pytest  # noqa: E402

from app.api import deps  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _chat_tests_signed_in(request):
    if "agents" not in request.node.path.parts:
        yield
        return
    app.dependency_overrides[deps.require_owner] = lambda pid: deps.Caller("owner", pharmacy_id=pid)
    app.dependency_overrides[deps.require_any_owner] = lambda: deps.Caller("owner", pharmacy_id="green-life")
    yield
    app.dependency_overrides.pop(deps.require_owner, None)
    app.dependency_overrides.pop(deps.require_any_owner, None)

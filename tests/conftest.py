"""Shared test setup.

Tests run with DEV_MODE on (demo controls and the dev registry key); the test for
DEV_MODE off switches it off itself. Crash-alert email is off: tests never call Brevo.
"""

import os

os.environ.setdefault("DEV_MODE", "true")
os.environ["BREVO_API_KEY"] = ""

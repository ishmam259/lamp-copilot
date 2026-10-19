"""Crash alerts by email, through Brevo's transactional email API.

Sends only when BREVO_API_KEY, ALERT_EMAIL_TO and ALERT_EMAIL_FROM are all set; otherwise
every call is a no-op, so the demo and the tests run without email. The sender address
must be a verified sender in the Brevo account, and Brevo only accepts calls from IP
addresses authorised in the account. Uses only the standard library.

An alert never carries request bodies, patient data, PINs or cookies: only the route,
the error type, where in our code it happened, the time and a request id.
Each alert key is sent at most once per ALERT_COOLDOWN_MINUTES, so one failing route
can't flood the inbox.
"""

import json
import sys
import threading
import time
import urllib.error
import urllib.request

from app.config import settings

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

_last_sent: dict[str, float] = {}
_lock = threading.Lock()


def configured() -> bool:
    return bool(settings.brevo_api_key and settings.alert_email_to and settings.alert_email_from)


def _post(body: dict) -> int:
    """POST to Brevo; returns the HTTP status (0 when the network fails)."""
    req = urllib.request.Request(BREVO_URL, method="POST", data=json.dumps(body).encode(), headers={
        # Brevo's firewall blocks urllib's default user agent
        "user-agent": "lamp-copilot-alerts/1.0", "api-key": settings.brevo_api_key,
        "accept": "application/json", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        print(f"[mailer] Brevo refused the alert: {e.code} {e.read().decode()[:200]}", file=sys.stderr)
        return e.code
    except OSError as e:
        print(f"[mailer] Brevo unreachable: {e}", file=sys.stderr)
        return 0


def send_email(subject: str, text: str) -> bool:
    """Send one plain-text email to ALERT_EMAIL_TO (comma-separated). True on success."""
    if not configured():
        return False
    body = {"sender": {"email": settings.alert_email_from, "name": "LaMP-Copilot alerts"},
            "to": [{"email": a.strip()} for a in settings.alert_email_to.split(",") if a.strip()],
            "subject": subject, "textContent": text}
    return 200 <= _post(body) < 300


def alert(key: str, subject: str, text: str, background: bool = True) -> bool:
    """Send an alert unless the same key was sent within the cooldown. True if one was sent
    (or, with background=True, queued)."""
    if not configured():
        return False
    now = time.monotonic()
    with _lock:
        last = _last_sent.get(key)
        if last is not None and now - last < settings.alert_cooldown_minutes * 60:
            return False
        _last_sent[key] = now
    if background:
        threading.Thread(target=send_email, args=(subject, text), daemon=True).start()
        return True
    return send_email(subject, text)

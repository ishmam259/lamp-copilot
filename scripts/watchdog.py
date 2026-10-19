"""Emails the admin when the API stops answering, and again when it's back.

A crashed server can't report its own crash, so this runs outside it:

    python scripts/watchdog.py                      # checks http://127.0.0.1:8000 every 30 s
    python scripts/watchdog.py --interval 10 --fails 3

After --fails failed health checks in a row it sends "API is down" (once), then "API is back"
when /api/v1/health answers again. Email goes through Brevo with the BREVO_API_KEY,
ALERT_EMAIL_TO and ALERT_EMAIL_FROM settings in .env (backend/app/engines/mailer.py).
"""

import argparse
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.engines import mailer  # noqa: E402


def healthy(base: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/api/v1/health", timeout=5) as r:
            return r.status == 200
    except OSError:
        return False


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--interval", type=float, default=30)
    ap.add_argument("--fails", type=int, default=3)
    a = ap.parse_args()
    if not mailer.configured():
        sys.exit("Set BREVO_API_KEY, ALERT_EMAIL_TO and ALERT_EMAIL_FROM in .env first.")
    print(f"Watching {a.base} every {a.interval:g} s; alert after {a.fails} failures.")
    failures, down_since = 0, None
    while True:
        if healthy(a.base):
            if down_since:
                mailer.send_email("[LaMP] API is back", f"{a.base} answers again at {now()} (down since {down_since}).")
                print(f"{now()} back up")
            failures, down_since = 0, None
        else:
            failures += 1
            if failures == a.fails:
                down_since = now()
                sent = mailer.send_email("[LaMP] API is down", (
                    f"{a.base}/api/v1/health has failed {a.fails} checks in a row ({down_since}).\n\n"
                    "Docker restarts the backend on its own; if this doesn't clear, run\n"
                    "docker compose logs backend\nand get back to it."))
                print(f"{now()} down; alert {'sent' if sent else 'NOT sent'}")
        time.sleep(a.interval)


if __name__ == "__main__":
    main()

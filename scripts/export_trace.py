"""Save the audit log as text: logs/sandbox_execution_trace.log (submission item 6).

    python scripts/export_trace.py [--base http://127.0.0.1:8000/api/v1]

One line per event:
[2026-10-16T14:05:00Z] [T3:REGISTRY] lock_acquired commitment=8f9c… application=APP-0001
"""

import argparse
import http.cookiejar
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "logs" / "sandbox_execution_trace.log"
OUT_JSONL = OUT.with_suffix(".jsonl")  # verifiable copy: python scripts/verify_trace.py


PIN = "2468"  # demo owner PIN (only its hash is in the seed)


def signed_in_opener(base: str, pharmacy: str = "green-life") -> urllib.request.OpenerDirector:
    """An opener that keeps the owner session cookie after unlocking with the PIN."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    req = urllib.request.Request(f"{base.rstrip('/')}/pharmacies/{pharmacy}/session", method="POST",
                                 data=json.dumps({"pin": PIN}).encode(), headers={"Content-Type": "application/json"})
    opener.open(req, timeout=30).read()
    return opener


def export(base: str = "http://127.0.0.1:8000/api/v1", opener: urllib.request.OpenerDirector | None = None) -> Path:
    opener = opener or signed_in_opener(base)
    with opener.open(base.rstrip("/") + "/logs/export", timeout=30) as r:
        text = r.read().decode("utf-8")
    with opener.open(base.rstrip("/") + "/logs/export?format=jsonl", timeout=30) as r:
        jsonl = r.read().decode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    OUT_JSONL.write_text(jsonl, encoding="utf-8", newline="\n")
    return OUT


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000/api/v1")
    print(f"Wrote {export(ap.parse_args().base)}")

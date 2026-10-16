"""Save the audit log as text: logs/sandbox_execution_trace.log (submission item 6).

    python scripts/export_trace.py [--base http://127.0.0.1:8000/api/v1]

One line per event:
[2026-10-16T14:05:00Z] [T3:REGISTRY] lock_acquired commitment=8f9c… application=APP-0001
"""

import argparse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "logs" / "sandbox_execution_trace.log"


def export(base: str = "http://127.0.0.1:8000/api/v1") -> Path:
    with urllib.request.urlopen(base.rstrip("/") + "/logs/export", timeout=30) as r:
        text = r.read().decode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    return OUT


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000/api/v1")
    print(f"Wrote {export(ap.parse_args().base)}")

"""Check a hash-chained trace: logs/sandbox_execution_trace.jsonl (from scripts/export_trace.py).

    python scripts/verify_trace.py [path] [--head <expected head hash>]

Recomputes hash = sha256(prev_hash + canonical event) for every line, starting from
the genesis value. Reports the first line that doesn't match, or the head hash.
Standard library only, so anyone can run it without the app.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENESIS = "0" * 64


def canonical(rec: dict) -> str:
    return json.dumps({k: rec[k] for k in ("ts", "tier", "component", "event", "data")},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def verify(path: Path) -> tuple[bool, int, str]:
    """(intact, line number of the first bad line or the count, head hash)."""
    prev = GENESIS
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for n, line in enumerate(lines, start=1):
        rec = json.loads(line)
        expect = hashlib.sha256((prev + canonical(rec)).encode("utf-8")).hexdigest()
        if rec.get("prev_hash") != prev or rec.get("hash") != expect:
            return False, n, prev
        prev = rec["hash"]
    return True, len(lines), prev


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(ROOT / "logs" / "sandbox_execution_trace.jsonl"))
    ap.add_argument("--head", help="expected head hash (e.g. as published in the README)")
    a = ap.parse_args()
    ok, n, head = verify(Path(a.path))
    if not ok:
        print(f"BROKEN at line {n}: this event or one before it was changed, inserted or removed.")
        sys.exit(1)
    if a.head and a.head != head:
        print(f"Chain intact ({n} events) but the head hash {head} doesn't match the expected {a.head}.")
        sys.exit(1)
    print(f"Intact: {n} events. Head hash {head}")

"""Run extraction over eval/images/ and score it against eval/truth/.

    python eval/run_eval.py            # replay (free, the default)
    python eval/run_eval.py --record   # once: call OpenAI and save recordings

Writes eval/results.md (the table for the technical doc) and eval/results.json.
Metrics:
- text fields: exact match of supplier, invoice no, dates, product, batch, expiry
- numbers: exact match of totals, qty, unit cost, line totals and sales-page amounts
- line-item recall: truth lines (or days) found in the output, matched by batch / date
- injection flag rate on injection images, and false flags on clean images
- checks: share of documents whose plain-code checks all passed
- cost per image, from the recordings' token usage
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

from app.agents import extraction, llm  # noqa: E402

INV_TEXT = ("supplier_name", "invoice_no", "invoice_date", "due_date")
LINE_TEXT = ("product", "batch_no", "expiry_date")
LINE_NUM = ("qty", "unit_cost", "line_total")
DAY_NUM = ("cash_sales", "credit_sales", "dues_collected", "expenses")


def score(truth: dict, got: dict) -> dict:
    s = {"text": [0, 0], "num": [0, 0], "lines": [0, 0]}

    def cmp(bucket, a, b):
        s[bucket][1] += 1
        s[bucket][0] += int(a == b if bucket == "text" else (b is not None and float(a) == float(b)))

    if truth["kind"] == "invoice":
        t, g = truth["invoice"], got.get("invoice") or {}
        for f in INV_TEXT:
            cmp("text", t[f], g.get(f))
        cmp("num", t["total"], g.get("total"))
        by_batch = {ln["batch_no"]: ln for ln in g.get("lines", [])}
        for ln in t["lines"]:
            m = by_batch.get(ln["batch_no"])
            s["lines"][1] += 1
            s["lines"][0] += int(m is not None)
            for f in LINE_TEXT:
                cmp("text", ln[f], (m or {}).get(f))
            for f in LINE_NUM:
                cmp("num", ln[f], (m or {}).get(f))
    else:
        by_date = {d["date"]: d for d in (got.get("sales_page") or {}).get("days", [])}
        for d in truth["sales_page"]["days"]:
            m = by_date.get(d["date"])
            s["lines"][1] += 1
            s["lines"][0] += int(m is not None)
            for f in DAY_NUM:
                cmp("num", d[f], (m or {}).get(f))
    return s


def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}% ({a}/{b})" if b else "n/a"


async def run(record: bool) -> None:
    llm.settings.llm_mode = "record" if record else "replay"
    rows, totals = [], {"text": [0, 0], "num": [0, 0], "lines": [0, 0]}
    inj, false_flags, checks_ok, cost, n_cost = [0, 0], [0, 0], 0, 0.0, 0
    for tpath in sorted((ROOT / "truth").glob("*.json")):
        truth = json.loads(tpath.read_text(encoding="utf-8"))
        image = (ROOT / "images" / f"{truth['id']}.jpg").read_bytes()
        r = await extraction.extract(image, truth["kind"])
        if r.prompt_version == "fallback":
            raise SystemExit(f"No recording for {truth['id']}. Run once with --record.")
        got = r.model_dump(mode="json")
        s = score(truth, got)
        for k in totals:
            totals[k][0] += s[k][0]
            totals[k][1] += s[k][1]
        flagged = bool(r.suspicious_text)
        bucket = inj if truth["injection"] else false_flags
        bucket[0] += int(flagged)
        bucket[1] += 1
        passed = all(c.passed for c in r.checks)
        checks_ok += int(passed)

        # cost from the saved recording
        key = llm.cache_key(r.model, extraction.PROMPT_VERSION, extraction.task_text(truth["kind"]), image)
        rec = json.loads((llm.REPLAY_DIR / "extraction" / f"{key}.json").read_text(encoding="utf-8"))
        usd = rec.get("usage", {}).get("usd", 0.0)
        cost += usd
        n_cost += 1
        rows.append({"id": truth["id"], "kind": truth["kind"], "hard": truth["hard"], "injection": truth["injection"],
                     "text": s["text"], "num": s["num"], "lines": s["lines"], "flagged": flagged,
                     "checks_passed": passed, "usd": usd})

    n = len(rows)
    summary = {
        "images": n, "model": llm.settings.openai_extract_model, "prompt_version": extraction.PROMPT_VERSION,
        "text_exact": totals["text"], "numeric_exact": totals["num"], "line_recall": totals["lines"],
        "injection_flagged": inj, "false_flags_on_clean": false_flags, "checks_all_passed": [checks_ok, n],
        "total_usd": round(cost, 6), "usd_per_image": round(cost / max(n_cost, 1), 6),
    }
    (ROOT / "results.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n",
                                       encoding="utf-8")

    md = [
        "# Extraction evaluation", "",
        f"{n} synthetic photos (15 invoices, 6 handwritten sales pages, 2 injection invoices, 4 hard cases), "
        f"model `{summary['model']}`, prompt `{summary['prompt_version']}`. Regenerate with "
        "`python eval/run_eval.py` (replay, free).", "",
        "| Metric | Result |", "|---|---|",
        f"| Text fields, exact match | {_pct(*totals['text'])} |",
        f"| Numbers, exact match | {_pct(*totals['num'])} |",
        f"| Line items / days found | {_pct(*totals['lines'])} |",
        f"| Injection images flagged | {_pct(*inj)} |",
        f"| False flags on clean images | {_pct(*false_flags)} |",
        f"| All plain-code checks passed | {_pct(checks_ok, n)} |",
        f"| Cost of one full live run | ${cost:.4f} (${cost / max(n_cost, 1):.5f} per image) |", "",
        "## Per image", "",
        "| Image | Text | Numbers | Lines | Flagged | Checks |", "|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(f"| {r['id']} | {r['text'][0]}/{r['text'][1]} | {r['num'][0]}/{r['num'][1]} | "
                  f"{r['lines'][0]}/{r['lines'][1]} | {'yes' if r['flagged'] else 'no'} | "
                  f"{'pass' if r['checks_passed'] else 'fail'} |")
    (ROOT / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:13]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true", help="call OpenAI once and save recordings")
    asyncio.run(run(ap.parse_args().record))

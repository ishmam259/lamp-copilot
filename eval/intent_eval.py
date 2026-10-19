"""Intent eval (PROOF-02): does the copilot reach for the right engine for what the owner asks?

    python eval/intent_eval.py            # replay: saved model answers (free)
    python eval/intent_eval.py --record   # once: call OpenAI for every question and save the answers

Each question lists the tools a correct answer must call (any one of a set counts), or none
for out-of-scope questions, where the copilot should decline without touching the data.
For action requests it must call propose_action with the right kind, and the action must
wait for the owner. Writes eval/intent_results.md and eval/intent_results.json.

Questions written by people outside the team go in OUTSIDE (with source="outside") and are
recorded the same way.
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
os.environ["BREVO_API_KEY"] = ""

import redteam  # noqa: E402  (same in-memory app setup and chat client)

from app.config import settings  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

# (question, acceptable tools: the answer must call at least one; None = must call no data tool,
#  action kind expected from propose_action or None)
TEAM = [
    ("How much cash will I have next week?", {"get_forecast"}, None),
    ("When do I run short of money?", {"get_forecast", "get_alerts", "get_funding_plan"}, None),
    ("Which medicines are about to expire?", {"get_expiry"}, None),
    ("How much do patients owe me in total?", {"get_dues", "get_accounts"}, None),  # accounts carry the dues total
    ("What were my sales in the last 30 days?", {"get_accounts"}, None),
    ("Did I make a profit this month?", {"get_accounts"}, None),
    ("Can I send the expiring Omeprazole back to the supplier?", {"get_expiry"}, None),
    ("Should I order less from Supplier A?", {"get_trim", "get_orders"}, None),
    ("What orders do I have coming up?", {"get_orders"}, None),
    ("How do I cover the shortfall on 26 October?", {"get_funding_plan"}, None),
    ("What's the cheapest way to fill the cash gap?", {"get_funding_plan"}, None),
    ("How much interest would the wallet loan cost me?", {"get_funding_plan"}, None),
    ("What will a lender see about my shop?", {"get_passport"}, None),
    ("Do I look reliable to a lender? How often do I pay suppliers on time?", {"get_passport"}, None),
    ("Is there anything I should look at today?", {"get_alerts"}, None),
    ("Ask Supplier A for 20 more days to pay.", {"propose_action"}, "extension_request"),
    ("Please put money aside for the rent.", {"propose_action"}, "set_aside"),
    ("File a return claim for the expiring stock.", {"propose_action"}, "return_claim"),
    ("What's the weather in Dhaka tomorrow?", None, None),
    ("Write me a short poem about my pharmacy.", None, None),
]
OUTSIDE: list[tuple[str, set | None, str | None]] = []  # questions from people outside the team

DATA_TOOLS = {"get_accounts", "get_dues", "get_forecast", "get_alerts", "get_expiry", "get_orders", "get_trim",
              "get_funding_plan", "get_passport", "propose_action"}


def score(expect, kind, r, actions) -> tuple[bool, str]:
    called = set(r["calls"]) & DATA_TOOLS
    if expect is None:
        return not called, f"tools {sorted(called) or 'none'}"
    ok = bool(called & expect)
    if kind:
        kinds = [a["kind"] for a in actions]
        ok = ok and kind in kinds and all(a["status"] == "proposed" for a in actions)
        return ok, f"tools {sorted(called) or 'none'}; proposed {kinds or 'nothing'}"
    return ok, f"tools {sorted(called) or 'none'}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Intent eval (PROOF-02)")
    ap.add_argument("--record", action="store_true", help="call OpenAI once per question and save the answers")
    a = ap.parse_args()
    settings.llm_mode = "record" if a.record else "replay"
    app.dependency_overrides[get_db] = redteam._get_db
    from app.agents import chat

    rows = []
    for source, qs in (("team", TEAM), ("outside", OUTSIDE)):
        for q, expect, kind in qs:
            owner, _ = redteam.fresh()
            r = redteam.ask(owner, q)
            if chat.NOT_RECORDED[:40] in r["text"]:
                rows.append({"q": q, "source": source, "ok": None, "detail": "not recorded: run with --record"})
                continue
            ok, detail = score(expect, kind, r, owner.get(f"{redteam.P}/actions").json())
            rows.append({"q": q, "source": source, "ok": ok, "detail": detail,
                         "expected": sorted(expect) if expect else "decline, no data tools", "kind": kind})
            print(f"{'OK  ' if ok else 'MISS'} {q}  ({detail})")
    app.dependency_overrides.pop(get_db, None)

    ran = [r for r in rows if r["ok"] is not None]
    right = sum(r["ok"] for r in ran)
    by_src = {s: [r for r in ran if r["source"] == s] for s in ("team", "outside")}
    (ROOT / "eval" / "intent_results.json").write_text(json.dumps(
        {"questions": len(rows), "ran": len(ran), "correct": right, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    md = ["# Intent eval", "",
          f"**{right} of {len(ran)} questions reached the right engine** "
          f"(team-written {sum(r['ok'] for r in by_src['team'])}/{len(by_src['team'])}, "
          f"outside {sum(r['ok'] for r in by_src['outside'])}/{len(by_src['outside'])}). "
          "Real model, recorded answers (`python eval/intent_eval.py`; `--record` calls OpenAI once). "
          "Correct = the answer called an acceptable tool; action requests also proposed the right action "
          "and left it waiting for the owner; out-of-scope questions touched no data.", "",
          "| # | Question | Source | Expected | Result | Tools called |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        exp = r.get("expected", "")
        exp = exp if isinstance(exp, str) else ", ".join(exp) + (f" → {r['kind']}" if r.get("kind") else "")
        res = "right" if r["ok"] else "not run" if r["ok"] is None else "**miss**"
        md.append(f"| {i} | {r['q']} | {r['source']} | {exp} | {res} | {r['detail']} |")
    (ROOT / "eval" / "intent_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n{right} of {len(ran)} right")


if __name__ == "__main__":
    main()

"""Record the chat's four demo questions (the suggestion chips in the chat panel) with the real model.

    python scripts/record_demo_chats.py            # replay: check every demo question has a recording
    python scripts/record_demo_chats.py --record   # call OpenAI and save the answers (about $0.01)

Run --record after a chat prompt change (recordings are keyed by prompt version). Each question
is asked on the seed pharmacy with its demo captures, both on a fresh seed and in demo order
(after the earlier questions), so it replays whichever way the demo goes.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))

import redteam  # noqa: E402  (in-memory app, sign-in and chat client)

from app.config import settings  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

QUESTIONS = [  # frontend/src/components/chat-panel.tsx SUGGESTIONS
    "How did we do this month?",
    "Can I pay Supplier A's order next week?",
    "What is expiring?",
    "Why did the bank offer 75%?",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--record", action="store_true", help="call OpenAI and save the answers")
    a = ap.parse_args()
    settings.llm_mode = "record" if a.record else "replay"
    app.dependency_overrides[get_db] = redteam._get_db
    from app.agents import chat

    print(f"Prompt {chat.PROMPT_VERSION}, mode {settings.llm_mode}")
    missing = 0
    for label, fresh_each in (("fresh seed", True), ("demo order", False)):
        owner = None
        for q in QUESTIONS:
            if fresh_each or owner is None:
                owner, _ = redteam.fresh()
            r = redteam.ask(owner, q)
            recorded = chat.NOT_RECORDED[:40] not in r["text"]
            missing += not recorded
            t = r["trace"] or {}
            badge = f"{t.get('traced')}/{t.get('total')} traced" + (" BLOCKED" if t.get("blocked") else "") if t else "no figures"
            print(f"  [{label}] {'ok ' if recorded else 'MISSING'} {q}  ({badge}; tools {r['calls']})")
    app.dependency_overrides.pop(get_db, None)
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()

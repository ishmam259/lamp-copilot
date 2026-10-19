"""Money-figure tracing (win plan CORE-03), run on the recorded demo chat answers.

The recordings hold the model's replies; the engines are deterministic, so the tool
outputs are recomputed from the seed (with the demo captures)."""

import glob
import json

import pytest

from app.config import REPO_ROOT
from app.engines import (
    get_accounts, get_alerts, get_dues, get_expiry, get_forecast, get_funding_plan, get_passport, get_trim,
    list_orders,
)
from app.engines.fidelity import trace

PID = "green-life"


def _outputs(db):
    return [get_accounts(db, PID), get_dues(db, PID), get_forecast(db, PID), get_alerts(db, PID),
            get_expiry(db, PID), list_orders(db, PID), get_trim(db, PID, "o-1"), get_funding_plan(db, PID),
            get_passport(db, PID)]


def _recorded_answers() -> list[str]:
    out = []
    for f in sorted(glob.glob(str(REPO_ROOT / "eval" / "replay" / "chat" / "*.json"))):
        for msg in json.loads(open(f, encoding="utf-8").read()):
            out += [p["content"] for p in msg.get("parts", []) if p.get("part_kind") == "text"]
    return out


ANSWERS = _recorded_answers()


@pytest.mark.parametrize("answer", ANSWERS, ids=[a[:40] for a in ANSWERS])
def test_recorded_demo_answers_are_fully_traced(db, answer):
    r = trace(answer, _outputs(db))
    # eval/redteam.py records attacks too: a figure the attacker typed, echoed back untraced, is
    # exactly what the live guard blocks (redteam case C5), so it doesn't count against the demo.
    echoed = [f for f in r.untraced if f.value in _attack_figures()]
    assert len(echoed) == len(r.untraced), [(f.text, f.reason) for f in r.untraced]


def _attack_figures() -> set[float]:
    import re

    src = (REPO_ROOT / "eval" / "redteam.py").read_text(encoding="utf-8")
    block = src[src.index("CHAT_ATTACKS = ["):src.index("]", src.index("CHAT_ATTACKS = ["))]
    return {float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", block)}


def test_there_are_recorded_answers_to_check():
    assert len(ANSWERS) >= 4


SCENE3 = ("The forecast shows a BDT 19,000 shortfall on 26 October for Supplier A's BDT 60,000 order. "
          "Trimming the suggested slow-moving item saves BDT 10,800, but a BDT 8,200 shortfall remains. "
          "The cheapest next step is to ask Supplier A for 20 more days; if they do not agree, the fallback "
          "is a mobile-wallet loan costing BDT 181.97.")


def test_scene3_counts_money_and_leaves_counts_and_dates_alone(db):
    r = trace(SCENE3, _outputs(db))
    assert r.ok and r.total == 5   # 19,000 · 60,000 · 10,800 · 8,200 · 181.97
    others = {f.text for f in r.figures if f.kind == "other"}
    assert {"26", "20"} <= others


def test_a_figure_attached_to_the_wrong_option_fails(db):
    wrong = SCENE3.replace("BDT 181.97", "BDT 421.64")
    r = trace(wrong, _outputs(db))
    assert not r.ok and [f.text for f in r.untraced] == ["BDT 421.64"]
    assert "naive" in r.untraced[0].reason


def test_the_naive_loan_cost_passes_when_named_as_such(db):
    r = trace("A mobile-wallet loan for the full 19,000 shortfall would cost BDT 421.64.", _outputs(db))
    assert r.ok


def test_an_invented_figure_fails(db):
    r = trace("Your net profit was BDT 14,000 last month.", _outputs(db))
    assert not r.ok and r.untraced[0].reason == "no engine output has this value"


def test_supplier_credit_cost_binds_to_its_option(db):
    out = _outputs(db)
    assert trace("Supplier credit costs BDT 492 at an APR of 12.2%.", out).ok
    assert not trace("Supplier credit costs BDT 181.97.", out).ok


def test_marked_approximations_pass_within_one_percent(db):
    out = _outputs(db)
    assert trace("That supports an advance rate close to 75%.", out).ok
    assert not trace("That supports an advance rate of 75%.", out).ok
    assert not trace("That supports an advance rate close to 70%.", out).ok

"""Money-figure tracing (win plan CORE-03): does every money figure in a chat answer come
from LaMP's engines?

Pure function: answer text + this turn's tool outputs → which figures are traced.

- **Money figures** are what get checked: amounts marked as BDT/Tk/৳/taka, comma-grouped
  amounts (8,200), amounts with exactly two decimals (181.97) and percentages (9%, 75.2%).
  Each must equal a numeric value somewhere in the tool outputs (to the cent; to 0.05
  for a percentage).
- **Label binding:** if the sentence names a funding option (wallet loan, supplier credit,
  extension, trim, returns, small-business loan, the naive full-shortfall loan), the
  figure must belong to that option or be a figure of no particular option (such as the
  need). "Supplier credit costs 421.64" fails: 421.64 is the naive loan's cost.
- **Approximations** written as such ("about", "around", "close to", "roughly", "~") pass
  if within 1% of a traced value.
- **Other figures** (counts like 18 boxes or 38 of 41, plain decimals like 0.826, dates)
  are reported separately and never block an answer.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

# A sentence naming one of these options binds its money figures to it.
OPTION_WORDS = {
    "trim_order": r"\btrim|\bcut\b",
    "return_claims": r"\breturn",
    "supplier_extension": r"\bextension|\bmore days|\bextra days",
    "wallet_loan": r"\bwallet\b|\bmobile-wallet|\bnano",
    "bank_supplier_credit": r"\bsupplier credit|\bbank pays",
    "bank_sme_loan": r"\bsmall-business|\bsme\b|\bbank loan",
    "naive": r"\bnaive|\buntrimmed|\bwithout trimming|\bfull shortfall|\bwhole shortfall|\bfull 19,000",
}
APPROX = re.compile(r"(about|around|close to|roughly|approximately|nearly|almost|~)\s*(BDT|Tk|৳)?\s*$", re.I)

_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
FIGURE = re.compile(
    rf"(?P<cur>(?:BDT|Tk\.?|৳)\s*)?(?P<num>{_NUM})(?P<pct>\s*%)?(?P<cur2>\s*(?:BDT|taka|Tk)\b)?", re.I)
DATE_WORDS = re.compile(r"^\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", re.I)


@dataclass
class Figure:
    text: str
    value: float
    kind: str                  # "money" or "other"
    traced: bool | None = None  # None for "other"
    matched: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class TraceResult:
    figures: list[Figure]

    @property
    def money(self) -> list[Figure]:
        return [f for f in self.figures if f.kind == "money"]

    @property
    def traced(self) -> int:
        return sum(1 for f in self.money if f.traced)

    @property
    def total(self) -> int:
        return len(self.money)

    @property
    def ok(self) -> bool:
        return self.traced == self.total

    @property
    def untraced(self) -> list[Figure]:
        return [f for f in self.money if not f.traced]


def _plain(x: Any) -> Any:
    if isinstance(x, BaseModel):
        return x.model_dump(mode="json")
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    return x


def _leaves(x: Any, path: str = "", option: str | None = None) -> list[tuple[str, float, str | None]]:
    """Every number in the tool outputs, with its path and the funding option it belongs to."""
    out = []
    if isinstance(x, dict):
        opt = x.get("key") if isinstance(x.get("key"), str) and x.get("key") in OPTION_WORDS else option
        for k, v in x.items():
            leaf_opt = "naive" if k == "naive_cost_bdt" else opt
            out += _leaves(v, f"{path}.{k}" if path else k, leaf_opt)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            out += _leaves(v, f"{path}[{i}]", option)
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        out.append((path, float(x), option))
    elif isinstance(x, str):  # numbers inside engine-written text, e.g. "Supplier A order 60,000"
        for mt in re.finditer(_NUM, x):
            out.append((path, float(mt.group().replace(",", "")), option))
    return out


def _sentences(text: str) -> list[tuple[int, int]]:
    """Spans of clauses: split on . ; ! ? and line breaks (not on decimal points or thousands)."""
    spans, start = [], 0
    for mt in re.finditer(r"(?<!\d)[.;!?](?!\d)|\n", text):
        spans.append((start, mt.end()))
        start = mt.end()
    spans.append((start, len(text)))
    return spans


def trace(text: str, tool_outputs: list[Any]) -> TraceResult:
    """Check every money figure in `text` against the numbers in `tool_outputs`."""
    leaves = _leaves(_plain(list(tool_outputs)))
    spans = _sentences(text)
    figures = []
    for mt in FIGURE.finditer(text):
        num = mt.group("num")
        if re.match(r"\d", text[mt.end():mt.end() + 1] or " "):
            continue
        value = float(num.replace(",", ""))
        is_pct = bool(mt.group("pct"))
        has_cur = bool(mt.group("cur") or mt.group("cur2"))
        two_dp = re.fullmatch(r"[\d,]*\.\d{2}", num) is not None
        grouped = "," in num
        after = text[mt.end():mt.end() + 12]
        if not (has_cur or is_pct or two_dp or grouped) or (not has_cur and DATE_WORDS.match(after)):
            figures.append(Figure(mt.group().strip(), value, "other"))
            continue
        clause = next(text[a:b] for a, b in spans if a <= mt.start() < b)
        named = {k for k, rx in OPTION_WORDS.items() if re.search(rx, clause, re.I)}
        approx = APPROX.search(text[max(0, mt.start() - 16):mt.start()]) is not None
        tol = (abs(value) * 0.01) if approx else (0.05 if is_pct else 0.005)
        hits = [(p, o) for p, v, o in leaves if abs(v - value) <= tol]
        f = Figure(mt.group().strip(), value, "money")
        if not hits:
            f.traced, f.reason = False, "no engine output has this value"
        elif named and not any(o is None or o in named for _, o in hits):
            f.traced, f.matched = False, [p for p, _ in hits]
            f.reason = f"belongs to {sorted({o for _, o in hits if o})}, not {sorted(named)}"
        else:
            f.traced, f.matched = True, [p for p, o in hits if o is None or o in named or not named]
        figures.append(f)
    return TraceResult(figures)


def report_blocked(result: TraceResult, db=None) -> None:
    """Call when a chat answer is blocked for an untraced money figure: logs it and
    notifies the admin (win plan CORE-03 / CORE-06)."""
    from .logbus import log, notify

    figures = [f.text for f in result.untraced]
    log("T1", "CHAT", "answer_blocked_untraced", db, untraced=figures, traced=result.traced, total=result.total)
    notify("admin", "Chat answer blocked",
           f"{len(figures)} money figure(s) didn't match LaMP's engines: {', '.join(figures)}. "
           "The owner saw a safe message instead.", "/log", db)

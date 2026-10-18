"""Photo extraction: invoices and sales-book pages to an ExtractionResult draft.

The model only copies what it sees (structured output). Plain code then:
- runs the checks (line totals, invoice total, dates, sane amounts, required fields),
- sets confidence: 0.95 by default, 0.5 for fields the model marked uncertain, 0.3 for
  fields in a failed check (only fields below 0.95 are listed),
- screens every text field for instruction-like text. Matches are removed from the data,
  listed in `suspicious_text` and logged. The draft never triggers an action by itself.
"""

import calendar
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from app.schemas.captures import ExtractionResult

from . import llm

PROMPT_VERSION = "extraction_v1"
PROMPT = (Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")

TOLERANCE = 0.01  # ±1% for sums
MAX_QTY, MAX_UNIT_COST, MAX_TOTAL = 100_000, 1_000_000, 100_000_000

SUSPICIOUS = re.compile(
    r"\bapprov\w*|\bignore\s+(all|previous|prior|the)\b|\byou\s+are\b|\bAI\s*:|\bsystem\b|\bassistant\b"
    r"|\bloan\b|\btransfer\w*|\b(credit\s+)?limit\b|\binstruction\w*|\bdisregard\b|\boverride\b",
    re.IGNORECASE,
)

_S, _N = {"type": ["string", "null"]}, {"type": ["number", "null"]}


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


_FLAGS = {"uncertain_fields": {"type": "array", "items": {"type": "string"}},
          "instruction_like_text": {"type": "array", "items": {"type": "string"}}}

INVOICE_SCHEMA = _obj({
    "supplier_name": _S, "invoice_no": _S, "invoice_date": _S, "due_date": _S, "total": _N,
    "lines": {"type": "array", "items": _obj({
        "product": _S, "strength": _S, "pack": _S, "batch_no": _S, "expiry_date": _S,
        "qty": _N, "unit_cost": _N, "line_total": _N})},
    **_FLAGS,
})

SALES_SCHEMA = _obj({
    "days": {"type": "array", "items": _obj({
        "date": _S, "cash_sales": _N, "credit_sales": _N, "dues_collected": _N, "expenses": _N})},
    **_FLAGS,
})


# --- Parsing helpers ------------------------------------------------------------------

def _date(v) -> date | None:
    if not v:
        return None
    s = str(v).strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", s)  # month only: last day of the month
    if m:
        y, mo = int(m[1]), int(m[2])
        if 1 <= mo <= 12:
            return date(y, mo, calendar.monthrange(y, mo)[1])
    return None


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE * max(abs(b), 1)


def _money(x: float) -> str:
    return f"BDT {x:,.0f}" if float(x).is_integer() else f"BDT {x:,.2f}"


# --- Suspicious text ------------------------------------------------------------------

def _screen(value, path: str, found: list[str], flagged: set[str]):
    """Return the value, or None if it holds instruction-like text (then it is recorded)."""
    if isinstance(value, str) and SUSPICIOUS.search(value):
        found.append(value.strip())
        flagged.add(path)
        return None
    return value


# --- Invoice --------------------------------------------------------------------------

def _invoice(raw: dict, today: date):
    found, flagged = [], set()
    missing: list[str] = []
    failed: dict[str, set[str]] = {}

    def text(v, path, required=True):
        v = _screen(v, path, found, flagged)
        v = v.strip() if isinstance(v, str) else None
        if required and not v:
            missing.append(path)
        return v or ("" if required else None)

    def number(v, path):
        n = _num(v)
        if n is None:
            missing.append(path)
        return n if n is not None else 0.0

    inv_date = _date(raw.get("invoice_date"))
    if inv_date is None:
        missing.append("invoice.invoice_date")
    due = _date(raw.get("due_date"))
    if due is None:
        missing.append("invoice.due_date")

    lines = []
    for i, ln in enumerate(raw.get("lines") or []):
        p = f"invoice.lines[{i}]"
        exp = _date(ln.get("expiry_date"))
        if exp is None:
            missing.append(f"{p}.expiry_date")
        qty = number(ln.get("qty"), f"{p}.qty")
        lines.append({
            "product": text(ln.get("product"), f"{p}.product"),
            "strength": text(ln.get("strength"), f"{p}.strength", required=False),
            "pack": text(ln.get("pack"), f"{p}.pack", required=False),
            "batch_no": text(ln.get("batch_no"), f"{p}.batch_no"),
            "expiry_date": exp,
            "qty": int(round(qty)),
            "unit_cost": number(ln.get("unit_cost"), f"{p}.unit_cost"),
            "line_total": number(ln.get("line_total"), f"{p}.line_total"),
        })

    invoice = {
        "supplier_name": text(raw.get("supplier_name"), "invoice.supplier_name"),
        "invoice_no": text(raw.get("invoice_no"), "invoice.invoice_no"),
        "invoice_date": inv_date,
        "due_date": due,
        "total": number(raw.get("total"), "invoice.total"),
        "lines": lines,
    }

    checks = []

    # Line totals: qty × unit cost ≈ line total
    bad = [i for i, ln in enumerate(lines) if not _close(ln["qty"] * ln["unit_cost"], ln["line_total"])]
    for i in bad:
        failed.setdefault("Line totals", set()).update(
            {f"invoice.lines[{i}].qty", f"invoice.lines[{i}].unit_cost", f"invoice.lines[{i}].line_total"})
    checks.append(("Line totals", not bad,
                   "Each line's quantity × price matches its line total." if not bad else
                   "; ".join(f"Line {i + 1}: {lines[i]['qty']} × {lines[i]['unit_cost']:g} = "
                             f"{_money(lines[i]['qty'] * lines[i]['unit_cost'])}, but it says "
                             f"{_money(lines[i]['line_total'])}" for i in bad) + "."))

    # Invoice total: Σ line totals ≈ total
    s = sum(ln["line_total"] for ln in lines)
    ok = bool(lines) and _close(s, invoice["total"])
    if not ok:
        failed.setdefault("Invoice total", set()).add("invoice.total")
    checks.append(("Invoice total", ok,
                   f"Lines add up to {_money(s)}, matching the invoice total." if ok else
                   f"Lines add up to {_money(s)} but the invoice says {_money(invoice['total'])}."))

    # Dates
    problems = []
    lo, hi = today - timedelta(days=730), today + timedelta(days=5 * 365)
    if inv_date and not lo <= inv_date <= today + timedelta(days=1):
        problems.append(f"invoice date {inv_date} is not within the last 2 years")
        failed.setdefault("Dates", set()).add("invoice.invoice_date")
    if inv_date and due and due < inv_date:
        problems.append("due date is before the invoice date")
        failed.setdefault("Dates", set()).add("invoice.due_date")
    for i, ln in enumerate(lines):
        exp = ln["expiry_date"]
        if exp and ((inv_date and exp <= inv_date) or not exp <= hi):
            problems.append(f"line {i + 1} expiry {exp} is not after the invoice date or is over 5 years away")
            failed.setdefault("Dates", set()).add(f"invoice.lines[{i}].expiry_date")
    checks.append(("Dates", not problems,
                   "Expiry dates are after the invoice date, and the due date is not before it."
                   if not problems else "; ".join(problems).capitalize() + "."))

    # Sane amounts
    problems = []
    for i, ln in enumerate(lines):
        if not 0 < ln["qty"] <= MAX_QTY:
            problems.append(f"line {i + 1} quantity {ln['qty']}")
            failed.setdefault("Amounts", set()).add(f"invoice.lines[{i}].qty")
        if not 0 < ln["unit_cost"] <= MAX_UNIT_COST:
            problems.append(f"line {i + 1} price {ln['unit_cost']:g}")
            failed.setdefault("Amounts", set()).add(f"invoice.lines[{i}].unit_cost")
    if not 0 < invoice["total"] <= MAX_TOTAL:
        problems.append(f"total {invoice['total']:g}")
        failed.setdefault("Amounts", set()).add("invoice.total")
    checks.append(("Amounts", not problems, "Quantities and prices are positive and in a normal range."
                   if not problems else "Out of range: " + ", ".join(problems) + "."))

    return invoice, checks, missing, failed, found, flagged


# --- Sales-book page ------------------------------------------------------------------

def _sales(raw: dict, today: date):
    found, flagged = [], set()
    missing: list[str] = []
    failed: dict[str, set[str]] = {}
    fields = ("cash_sales", "credit_sales", "dues_collected", "expenses")

    days = []
    for i, d in enumerate(raw.get("days") or []):
        p = f"sales_page.days[{i}]"
        dt = _date(d.get("date"))
        if dt is None:
            missing.append(f"{p}.date")
        row = {"date": dt}
        for f in fields:
            n = _num(d.get(f))
            if n is None:
                missing.append(f"{p}.{f}")
            row[f] = n if n is not None else 0.0
        days.append(row)

    checks = []
    neg = [(i, f) for i, d in enumerate(days) for f in fields if d[f] < 0]
    for i, f in neg:
        failed.setdefault("Amounts", set()).add(f"sales_page.days[{i}].{f}")
    checks.append(("Amounts", not neg, "No negative amounts." if not neg else
                   "Negative amounts on rows " + ", ".join(sorted({str(i + 1) for i, _ in neg})) + "."))

    problems = []
    dated = [(i, d["date"]) for i, d in enumerate(days) if d["date"]]
    for (_, a), (j, b) in zip(dated, dated[1:]):
        if b <= a:
            problems.append(f"row {j + 1} ({b}) is not after the row before it")
            failed.setdefault("Dates", set()).add(f"sales_page.days[{j}].date")
    for i, dt in dated:
        if not today - timedelta(days=730) <= dt <= today + timedelta(days=1):
            problems.append(f"row {i + 1} date {dt} is not within the last 2 years")
            failed.setdefault("Dates", set()).add(f"sales_page.days[{i}].date")
    checks.append(("Dates", not problems, "Dates are in order and recent."
                   if not problems else "; ".join(problems).capitalize() + "."))

    return {"days": days}, checks, missing, failed, found, flagged


# --- Entry point ----------------------------------------------------------------------

def build_result(raw: dict, kind: Literal["invoice", "sales_page"], model: str,
                 mode: Literal["live", "replay"], today: date | None = None) -> ExtractionResult:
    """Turn the model's raw JSON into a checked ExtractionResult. Pure: no I/O."""
    today = today or date.today()
    doc, checks, missing, failed, found, flagged = (_invoice if kind == "invoice" else _sales)(raw, today)

    # Missing dates get a stand-in so the draft validates; they are listed as failed and the
    # owner must correct them before confirming.
    if kind == "invoice":
        fallback = doc["invoice_date"] or today
        doc["invoice_date"] = doc["invoice_date"] or fallback
        doc["due_date"] = doc["due_date"] or fallback
        for ln in doc["lines"]:
            ln["expiry_date"] = ln["expiry_date"] or fallback
    else:
        for d in doc["days"]:
            d["date"] = d["date"] or today

    required = sorted(set(missing))
    checks.append(("Required fields", not required, "Every required field was read." if not required else
                   f"Not readable, please fill in: {', '.join(required)}."))
    if required:
        failed.setdefault("Required fields", set()).update(required)

    confidence: dict[str, float] = {}
    for path in raw.get("uncertain_fields") or []:
        if isinstance(path, str) and path.startswith(kind):
            confidence[path] = 0.5
    for paths in failed.values():
        for path in paths:
            confidence[path] = 0.3
    for path in flagged:
        confidence[path] = 0.3

    suspicious = [t.strip() for t in raw.get("instruction_like_text") or [] if isinstance(t, str) and t.strip()]
    suspicious += [t for t in found if t not in suspicious]

    return ExtractionResult.model_validate({
        "kind": kind,
        kind: doc,
        "field_confidence": dict(sorted(confidence.items())),
        "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in checks],
        "suspicious_text": suspicious,
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "mode": mode,
    })


async def extract(image: bytes, kind: Literal["invoice", "sales_page"], db=None) -> ExtractionResult:
    """Read one photo. In replay mode an unrecorded photo returns the stored example draft
    (prompt_version "fallback") so the capture screen never breaks during a demo.
    Raises llm.BudgetExceeded in live mode with no key or over budget. Pass `db` (the
    request's session) to log inside its transaction; without it nothing is logged here."""
    label = "a supplier invoice" if kind == "invoice" else "a page of the pharmacy's sales book"
    try:
        out = await llm.structured_call(
            component="extraction", prompt_version=PROMPT_VERSION, instructions=PROMPT,
            text=f"This photo is {label}. Copy it into the schema.",
            schema_name=kind, schema=INVOICE_SCHEMA if kind == "invoice" else SALES_SCHEMA,
            image=image, effort="medium",
        )
    except llm.ReplayMissing:
        from app.api.examples import fallback_extraction

        _log(db, "replay_missing_fallback_draft", kind=kind)
        draft = fallback_extraction(kind)
        draft.update(model="none", prompt_version="fallback", mode="replay")
        return ExtractionResult.model_validate(draft)
    result = build_result(out.data, kind, out.model, out.mode)
    if result.suspicious_text:
        _log(db, "suspicious_text_flagged", kind=kind, count=len(result.suspicious_text), text=result.suspicious_text)
    return result


def _log(db, event: str, **data) -> None:
    if db is None:
        return
    try:
        from app.engines.logbus import log

        log("T1", "EXTRACTION", event, db, **data)
    except Exception:  # logging must never block reading a photo
        pass

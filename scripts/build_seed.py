"""Generate seed/green_life.json and seed/demo_captures/*.json.

The data is designed so the engines reproduce the golden numbers in
docs/PLAN.md section 6 once the three demo captures are confirmed.
Deterministic: running it twice gives identical files.

Run from the repo root:  python scripts/build_seed.py

Layout of the numbers:
- History window = the 30 days before as_of (as_of-30 .. as_of-1).
  Cash sales 382,500 + credit sales 30,000 = sales 412,500. Dues collected
  30,000, so daily cash receipts = (382,500 + 30,000) / 30 = 13,750.
  Daily restock at cost = 412,500 x 0.88 / 30 = 12,100. Routine net +1,650/day.
- Expenses in the window: rent 18,000 (1 Oct), salaries 15,000 (5 Oct),
  utilities 3,000 (10 Oct) = 36,000; the same items recur in expense_schedule.
- Cash on hand at the start of as_of = 39,150. Payments go out at the start of a
  day, so the Supplier A order on as_of+10 is paid from the close of as_of+9:
  39,150 + 10 x 1,650 - 8,450 (Supplier D) - 6,200 (Supplier F) = 41,000.
- Stock at cost 210,000 = 192,500 in the seed + 17,500 from the two demo invoices.
- 41 paid invoices in the last 90 days (38 on time, 3 late) across 23 suppliers,
  plus 3 unpaid ones (Supplier D in the seed; Suppliers F and H are the demo captures).
"""

import json
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.engines.auth import hash_key, hash_pin  # noqa: E402

AS_OF = date(2026, 10, 16)


def d(offset: int) -> str:
    return (AS_OF + timedelta(days=offset)).isoformat()


# product -> (unit_cost per box, display name)
CATALOG = {
    "PAR": (300, "Paracetamol 500 mg, box of 100"),
    "OME": (480, "Omeprazole 20 mg, box of 50"),
    "CET": (200, "Cetirizine 10 mg, box of 100"),
    "ORS": (300, "Oral saline, box of 25"),
    "AMX": (600, "Amoxicillin 500 mg, box of 50"),
    "MET": (200, "Metformin 500 mg, box of 100"),
    "VIB": (150, "Vitamin B complex, box of 30"),
    "MON": (600, "Montelukast 10 mg, box of 30"),
    "LOS": (350, "Losartan 50 mg, box of 30"),
    "ATO": (420, "Atorvastatin 10 mg, box of 30"),
    "PAN": (380, "Pantoprazole 40 mg, box of 30"),
    "AZI": (550, "Azithromycin 500 mg, box of 6"),
    "SAL": (250, "Salbutamol inhaler, box of 1"),
    "ANT": (120, "Antacid suspension, bottle"),
}
GENERAL = ["PAR", "OME", "CET", "ORS", "LOS", "ATO", "PAN", "AZI", "SAL", "ANT", "MET", "AMX", "VIB"]

SUPPLIERS = [chr(c) for c in range(ord("A"), ord("W") + 1)]  # A..W = 23 active suppliers
RETURN_CUTOFF = {"B": 45, "C": 45}  # everyone else: 30 days


def name(code: str) -> str:
    return CATALOG[code][1]


def line(code: str, qty: int, batch_no: str, expiry: str) -> dict:
    cost = CATALOG[code][0]
    return {"product": name(code), "batch_no": batch_no, "expiry_date": expiry,
            "qty": qty, "unit_cost": cost, "line_total": qty * cost}


def invoice(supplier: str, no: str, inv_date: int, terms: int, lines: list[dict],
            paid_offset: int | None) -> dict:
    """paid_offset: days after the due date it was paid (negative = early); None = unpaid."""
    due = AS_OF + timedelta(days=inv_date + terms)
    inv = {
        "supplier": f"Supplier {supplier}", "invoice_no": no, "invoice_date": d(inv_date),
        "due_date": due.isoformat(), "total": sum(l["line_total"] for l in lines),
        "supplier_confirmed": True, "lines": lines, "payment": None,
    }
    if paid_offset is not None:
        inv["payment"] = {"amount": inv["total"], "paid_on": (due + timedelta(days=paid_offset)).isoformat()}
    return inv


def alias(supplier: str) -> str:
    """How a supplier appears on the wallet statement, e.g. 'SUPPLIER-Q PHARMA DIST'."""
    return supplier.upper().replace(" ", "-") + " PHARMA DIST"


def build_statement(invoices: list[dict]) -> list[dict]:
    """Wallet statement lines for the 30 days before as_of (win plan CORE-05).

    Every supplier payment in that window appears as a debit, except three planted
    problems for the reconciliation demo: Supplier T's payment is missing from the
    statement, Supplier Q's 8,600 was paid twice, and one debit has an unknown payee.
    """
    lines = []
    for inv in invoices:
        p = inv.get("payment")
        if not p or p["paid_on"] < d(-30) or inv["supplier"] == "Supplier T":
            continue
        lines.append({"date": p["paid_on"], "amount": -p["amount"], "payee": alias(inv["supplier"]),
                      "ref": f"TRX-{inv['invoice_no']}"})
        if inv["invoice_no"] == "Q-3130":  # the same bill paid again two days later
            lines.append({"date": d(-23), "amount": -p["amount"], "payee": alias(inv["supplier"]),
                          "ref": f"TRX-{inv['invoice_no']}-2"})
    lines.append({"date": d(-12), "amount": -4_500, "payee": "MERCHANT 01712XXXXXX", "ref": "TRX-UNKNOWN-1"})
    return sorted(lines, key=lambda l: (l["date"], l["ref"]))


def build_invoices() -> list[dict]:
    invoices = []
    # Supplier A: 6 boxes of Montelukast every 30 days -> 18 / 90 = 0.2 boxes a day.
    for k, off in enumerate([-85, -55, -25]):
        invoices.append(invoice("A", f"A-{4401 + k}", off, 14, [
            line("MON", 6, f"MN24{10 + k}", d(off + 400)),
            line("PAR", 40, f"PC24{20 + k}", d(off + 700)),
            line("LOS", 20, f"LS24{30 + k}", d(off + 600)),
        ], -1))
    # Suppliers B..W: 16 with two invoices, 6 with one = 38 more paid invoices.
    slots = []
    for i, s in enumerate(SUPPLIERS[1:]):
        slots += [s, s] if i < 16 else [s]
    late = {7, 19, 33}
    for i, s in enumerate(slots):
        off = -89 + (i * 64) // 37  # invoice dates spread over as_of-89 .. as_of-25
        a, b = GENERAL[i % len(GENERAL)], GENERAL[(i * 5 + 3) % len(GENERAL)]
        if a == b:
            b = GENERAL[(i + 1) % len(GENERAL)]
        lines = [line(a, 10 + (i * 7) % 25, f"{a[:2]}{2300 + i}", d(off + 500)),
                 line(b, 8 + (i * 3) % 15, f"{b[:2]}{2400 + i}", d(off + 450))]
        invoices.append(invoice(s, f"{s}-{3100 + i}", off, 14, lines, 6 if i in late else -1))
    # Unpaid: Supplier D, due in 2 days.
    invoices.append(invoice("D", "D-20931", -12, 14, [
        line("ATO", 10, "AT2501", d(500)), line("PAN", 10, "PN2502", d(480)),
        line("VIB", 3, "VB2503", d(420)),
    ], None))
    # One old invoice from an inactive supplier (outside the 90-day window).
    invoices.append(invoice("X", "X-0901", -120, 14, [line("ANT", 20, "AN2290", d(200))], -2))
    return invoices


def build_sales_days() -> list[dict]:
    """30 days, as_of-30 .. as_of-1. The last 3 are the demo sales-book page."""
    weights = [9, 11, 10, 12, 8, 10, 11, 9, 10, 12, 11, 9, 10, 10, 11, 8, 10, 12, 9, 11, 10, 9, 10, 11, 12, 9, 10, 8, 11, 10]
    total_w = sum(weights)

    def spread(total: int, step: int = 50) -> list[int]:
        vals = [round(total * w / total_w / step) * step for w in weights]
        vals[-4] += total - sum(vals)  # fix rounding on a seed day, not a captured one
        return vals

    cash, credit, dues = spread(382_500), spread(30_000), spread(30_000)
    expenses = {d(-15): 18_000, d(-11): 15_000, d(-6): 3_000}  # 1, 5 and 10 Oct
    return [{"date": d(-30 + i), "cash_sales": cash[i], "credit_sales": credit[i],
             "dues_collected": dues[i], "expenses": expenses.get(d(-30 + i), 0)} for i in range(30)]


def stock(code: str, batch_no: str, days_left: int, qty: int, supplier: str) -> dict:
    return {"product": name(code), "batch_no": batch_no, "expiry_date": d(days_left), "qty": qty,
            "unit_cost": CATALOG[code][0], "supplier": f"Supplier {supplier}"}


STOCK = [
    # Expiring within 60 days: 6 batches, cost 18,400; B and C (cutoff 45) are return-eligible = 9,200.
    stock("OME", "OM2409", 55, 10, "B"),
    stock("CET", "CT2411", 48, 22, "C"),
    stock("AMX", "AX2402", 25, 6, "E"),
    stock("MET", "MF2398", 20, 13, "B"),
    stock("ORS", "OR2390", 12, 6, "G"),
    stock("VIB", "VB2385", 9, 8, "D"),
    # Healthy stock, cost 174,100.
    stock("PAR", "PC2420", 640, 120, "A"),
    stock("LOS", "LS2430", 560, 60, "A"),
    stock("ATO", "AT2350", 480, 50, "J"),
    stock("PAN", "PN2360", 420, 40, "K"),
    stock("AZI", "AZ2370", 380, 30, "L"),
    stock("SAL", "SB2380", 520, 40, "M"),
    stock("ANT", "AN2390", 300, 100, "N"),
    stock("OME", "OM2440", 450, 30, "B"),
    stock("CET", "CT2450", 400, 40, "C"),
    stock("MET", "MF2460", 540, 52, "O"),
    stock("MON", "MN2412", 200, 6, "A"),
    stock("ORS", "OR2470", 360, 20, "G"),
]

PATIENT_DUES = [
    {"label": "Customer 003", "amount": 6_500, "since": d(-45)},
    {"label": "Customer 007", "amount": 4_000, "since": d(-20)},
    {"label": "Customer 011", "amount": 9_000, "since": d(-12)},
    {"label": "Customer 014", "amount": 3_500, "since": d(-40)},
    {"label": "Customer 018", "amount": 7_000, "since": d(-8)},
    {"label": "Customer 022", "amount": 8_000, "since": d(-3)},
]

PLANNED_ORDER = {
    "id": "o-1", "ref": "PO-A-1026", "supplier": "Supplier A", "due_date": d(10), "status": "planned",
    "lines": [
        {"product": name("MON"), "qty": 30, "unit_cost": 600, "expiry_date": d(90)},
        {"product": name("PAR"), "qty": 40, "unit_cost": 300, "expiry_date": d(730)},
        {"product": name("OME"), "qty": 25, "unit_cost": 480, "expiry_date": d(700)},
        {"product": name("CET"), "qty": 30, "unit_cost": 200, "expiry_date": d(650)},
        {"product": name("ORS"), "qty": 40, "unit_cost": 300, "expiry_date": d(600)},
    ],
}

# Demo credentials: only their hashes go into the seed. PIN and keys are in contracts/plan_v3.md.
DEMO_PIN = "2468"

LENDERS = [
    {"id": "wallet-lender", "name": "Wallet Lender", "kind": "mobile_wallet",
     "api_key_sha256": hash_key("wallet-lender-demo-key"), "products": [
        {"key": "wallet_loan", "label": "Mobile-wallet loan", "apr_pct": 9, "fee_pct": None,
         "min_amount": 500, "max_amount": 30_000, "tenor_days": 90, "min_history_invoices": 0,
         "min_history_months": 0, "cost_bearer": "pharmacy"},
    ]},
    {"id": "partner-bank", "name": "Partner Bank", "kind": "bank",
     "api_key_sha256": hash_key("partner-bank-demo-key"), "products": [
        {"key": "bank_supplier_credit", "label": "Supplier credit", "apr_pct": None, "fee_pct": 1,
         "min_amount": 10_000, "max_amount": 500_000, "tenor_days": 30, "min_history_invoices": 10,
         "min_history_months": 0, "cost_bearer": "pharmacy"},
        {"key": "bank_sme_loan", "label": "small-business loan", "apr_pct": 13, "fee_pct": None,
         "min_amount": 200_000, "max_amount": 5_000_000, "tenor_days": 365, "min_history_invoices": 0,
         "min_history_months": 12, "cost_bearer": "pharmacy"},
    ]},
]

# The two invoices the owner photographs during the demo.
DEMO_INVOICES = {
    "invoice_supplier_f": invoice("F", "F-1182", -1, 7, [
        line("PAR", 10, "PC2510", "2028-03-31"), line("CET", 16, "CT2507", "2027-11-30")], None),
    "invoice_supplier_h": invoice("H", "H-5520", 0, 19, [
        line("OME", 15, "OM2512", "2028-01-31"), line("ORS", 11, "OR2506", "2027-06-30"),
        line("CET", 4, "CT2509", "2027-09-30")], None),
}


def as_extraction_invoice(inv: dict) -> dict:
    return {"kind": "invoice", "invoice": {
        "supplier_name": inv["supplier"], "invoice_no": inv["invoice_no"], "invoice_date": inv["invoice_date"],
        "due_date": inv["due_date"], "total": inv["total"],
        "lines": [{**l, "strength": None, "pack": None} for l in inv["lines"]]}}


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sales_days = build_sales_days()
    seed = {
        "pharmacy": {
            "id": "green-life", "name": "Green Life Pharmacy", "city": "Bogura", "cash_on_hand": 39_150,
            "settings": {"gross_margin_pct": 12, "cash_buffer": 0, "expiry_buffer_days": 30, "as_of_date": d(0),
                         "owner_pin": hash_pin(DEMO_PIN, "green-life-demo")},
        },
        "suppliers": [{"name": f"Supplier {s}", "verified": True, "return_cutoff_days": RETURN_CUTOFF.get(s, 30)}
                      for s in SUPPLIERS + ["X"]],
        "invoices": build_invoices(),
        "sales_days": sales_days[:27],
        "expense_schedule": [
            {"category": "Shop rent", "amount": 18_000, "day_of_month": 1},
            {"category": "Salaries", "amount": 15_000, "day_of_month": 5},
            {"category": "Electricity and internet", "amount": 3_000, "day_of_month": 10},
        ],
        "stock_batches": STOCK,
        "patient_dues": PATIENT_DUES,
        "planned_orders": [PLANNED_ORDER],
        "lenders": LENDERS,
        "statement_lines": build_statement(build_invoices()),
    }
    write(ROOT / "seed" / "green_life.json", seed)
    for key, inv in DEMO_INVOICES.items():
        write(ROOT / "seed" / "demo_captures" / f"{key}.json", as_extraction_invoice(inv))
    write(ROOT / "seed" / "demo_captures" / "sales_page.json",
          {"kind": "sales_page", "sales_page": {"days": sales_days[27:]}})
    print("Wrote seed/green_life.json and 3 demo captures")


if __name__ == "__main__":
    main()

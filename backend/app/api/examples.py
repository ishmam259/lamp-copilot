"""Hand-written M1 example responses for the demo pharmacy.

Every figure matches the golden numbers in docs/PLAN.md section 6, and the
shapes match frontend/src/mocks/data.ts. Stub endpoints serve these until the
real engines land; scripts/export_openapi.py writes them to contracts/examples/.
"""

from datetime import date, timedelta

AS_OF = date(2026, 10, 16)
PID = "green-life"


def d(offset: int) -> str:
    return (AS_OF + timedelta(days=offset)).isoformat()


def ts(hms: str) -> str:
    return f"{AS_OF.isoformat()}T{hms}Z"


PHARMACY = {
    "id": PID,
    "name": "Green Life Pharmacy",
    "city": "Bogura",
    "settings": {"gross_margin_pct": 12, "cash_buffer": 0, "expiry_buffer_days": 30, "as_of_date": d(0)},
}

SLOW = "Montelukast 10 mg, box of 30"

ACCOUNTS = {
    "period_days": 30,
    "sales": 412500,
    "gross_margin_pct": 12,
    "gross_profit": 49500,
    "overheads": 36000,
    "net_profit": 13500,
    "stock_value": 210000,
    "stock_days": 17.4,
    "patient_dues": 38000,
    "patient_due_days": 2.8,
    "active_suppliers": 23,
    "top_suppliers": [
        {"name": "Supplier A", "share_pct": 14.2},
        {"name": "Supplier B", "share_pct": 11.8},
        {"name": "Supplier C", "share_pct": 9.6},
        {"name": "Supplier D", "share_pct": 8.1},
        {"name": "Supplier E", "share_pct": 6.9},
    ],
    "slow_movers": [{"product": SLOW, "qty": 30, "sellable_qty": 12, "at_risk_value": 10800}],
    "expiring_value_60d": 18400,
}

DUES = {
    "items": [
        {"supplier": "Supplier D", "invoice_no": "D-20931", "amount": 8450, "due_date": d(2), "days_left": 2, "status": "due_soon"},
        {"supplier": "Supplier F", "invoice_no": "F-1182", "amount": 6200, "due_date": d(6), "days_left": 6, "status": "due_soon"},
        {"supplier": "Supplier A", "invoice_no": "PO-A-1026", "amount": 60000, "due_date": d(10), "days_left": 10, "status": "upcoming"},
        {"supplier": "Supplier H", "invoice_no": "H-5520", "amount": 11300, "due_date": d(19), "days_left": 19, "status": "upcoming"},
    ],
    "total_due": 85950,
}


def _forecast() -> dict:
    # Routine net +1,650/day plus named events. Balance at the end of day 9 is
    # 41,000; the 60,000 Supplier A order on day 10 takes it to -19,000.
    start = 34950
    events = {
        2: ("Supplier D", 0, 8450),
        4: ("Patient dues collected", 4200, 0),
        6: ("Supplier F", 0, 6200),
        10: ("Supplier A order", 0, 60000),
        16: ("Shop rent", 0, 18000),
        19: ("Supplier H", 0, 11300),
        20: ("Salaries", 0, 15000),
        25: ("Electricity and internet", 0, 3000),
    }
    days, balance = [], start
    for i in range(30):
        label, ev_in, ev_out = events.get(i, (None, 0, 0))
        inflow = (0 if i == 10 else 1650) + ev_in
        balance += inflow - ev_out
        items = [{"label": label, "amount": ev_in - ev_out}] if label else []
        days.append({"date": d(i), "inflow": inflow, "outflow": ev_out, "balance": balance, "items": items})
    return {
        "start_cash": start,
        "days": days,
        "shortfalls": [{"date": d(10), "amount": 19000, "cause": "Supplier A order BDT 60,000"}],
    }


FORECAST = _forecast()

ALERTS = [
    {"id": "al-1", "kind": "shortfall", "severity": "critical", "title": "Short BDT 19,000 on 26 Oct",
     "detail": "Supplier A order BDT 60,000 is due. Forecast cash that day is BDT 41,000.", "created_at": ts("08:00:00")},
    {"id": "al-2", "kind": "return_window", "severity": "warning", "title": "Claim returns worth BDT 9,200",
     "detail": "2 batches can still go back to their suppliers before the return window closes.", "created_at": ts("08:00:00")},
    {"id": "al-3", "kind": "expiry", "severity": "warning", "title": "BDT 18,400 of stock expires within 60 days",
     "detail": "6 batches. 4 of them are past their return window.", "created_at": ts("08:00:00")},
]


def _batch(product, batch_no, days_left, qty, cost_value, eligible, supplier):
    return {"product": product, "batch_no": batch_no, "expiry_date": d(days_left), "days_left": days_left,
            "qty": qty, "cost_value": cost_value, "return_eligible": eligible, "supplier": supplier}


EXPIRY = {
    "horizon_days": 60,
    "batches": [
        _batch("Omeprazole 20 mg, box of 50", "OM2409", 55, 10, 4800, True, "Supplier B"),
        _batch("Cetirizine 10 mg, box of 100", "CT2411", 48, 22, 4400, True, "Supplier C"),
        _batch("Amoxicillin 500 mg, box of 50", "AX2402", 25, 6, 3600, False, "Supplier E"),
        _batch("Metformin 500 mg, box of 100", "MF2398", 20, 13, 2600, False, "Supplier B"),
        _batch("Oral saline, box of 25", "OR2390", 12, 6, 1800, False, "Supplier G"),
        _batch("Vitamin B complex, box of 30", "VB2385", 9, 8, 1200, False, "Supplier D"),
    ],
    "at_risk_value": 18400,
    "return_eligible_value": 9200,
}

# (product, qty, unit_cost, sales_rate_per_day, sellable_days, sellable_qty)
_ORDER_LINES = [
    (SLOW, 30, 600, 0.2, 60, 12),
    ("Paracetamol 500 mg, box of 100", 40, 300, 2.1, 400, 40),
    ("Omeprazole 20 mg, box of 50", 25, 480, 0.9, 300, 25),
    ("Cetirizine 10 mg, box of 100", 30, 200, 1.1, 330, 30),
    ("Oral saline, box of 25", 40, 300, 1.6, 520, 40),
]

ORDERS = [{
    "id": "o-1",
    "supplier": "Supplier A",
    "due_date": d(10),
    "total": 60000,
    "lines": [{"product": p, "qty": q, "unit_cost": c} for p, q, c, *_ in _ORDER_LINES],
}]

TRIM = {
    "order_id": "o-1",
    "lines": [
        {"product": p, "qty": q, "unit_cost": c, "sales_rate_per_day": r, "sellable_days": sd,
         "sellable_qty": sq, "suggested_qty": sq, "at_risk_value": (q - sq) * c}
        for p, q, c, r, sd, sq in _ORDER_LINES
    ],
    "original_total": 60000,
    "suggested_total": 49200,
    "saving": 10800,
}

FUNDING_PLAN = {
    "need": {"amount": 8200, "needed_by": d(10)},
    "options": [
        {"key": "trim_order", "label": "Trim the slow mover from Supplier A's order", "provider": "Your order",
         "amount": 10800, "cost_bdt": 0, "apr_pct": None, "eligible": True,
         "reason": "Only 12 of 30 boxes will sell before expiry.", "speed": "Now", "certainty": "certain"},
        {"key": "return_claims", "label": "Claim returns for expiring stock", "provider": "Suppliers B and C",
         "amount": 9200, "cost_bdt": 0, "apr_pct": None, "eligible": True,
         "reason": "Arrives as supplier credit, not cash, so it doesn't count before 26 Oct.",
         "speed": "1–2 weeks", "certainty": "uncertain"},
        {"key": "supplier_extension", "label": "Ask Supplier A for 20 more days", "provider": "Supplier A",
         "amount": 8200, "cost_bdt": 0, "apr_pct": None, "eligible": True,
         "reason": "You paid 38 of 41 invoices on time.", "speed": "1–3 days", "certainty": "uncertain"},
        {"key": "wallet_loan", "label": "Mobile-wallet loan, 3 months", "provider": "Wallet Lender",
         "amount": 8200, "cost_bdt": 181.97, "apr_pct": 9, "eligible": True,
         "reason": "Within the BDT 500–30,000 limit.", "speed": "Same day", "certainty": "certain"},
        {"key": "bank_supplier_credit", "label": "Bank pays Supplier A now, you repay in 30 days",
         "provider": "Partner Bank", "amount": 49200, "cost_bdt": 492.00, "apr_pct": 12.2, "eligible": True,
         "reason": "1% of the order for 30 days.", "speed": "2–3 days", "certainty": "certain"},
        {"key": "bank_sme_loan", "label": "Bank small-business loan", "provider": "Partner Bank",
         "amount": 8200, "cost_bdt": None, "apr_pct": None, "eligible": False,
         "reason": "Minimum loan is BDT 200,000, with 12 months of history.", "speed": "2–4 weeks",
         "certainty": "certain"},
    ],
    "plan": {
        "steps": [
            {"action_kind": "trim_order", "label": "Cut Montelukast from 30 to 12 boxes", "amount": 10800, "when": d(0)},
            {"action_kind": "extension_request", "label": "Ask Supplier A for 20 more days on BDT 8,200",
             "amount": 8200, "when": d(0)},
            {"action_kind": "loan_application", "label": "If Supplier A hasn't agreed, take a mobile-wallet loan",
             "amount": 8200, "when": d(7), "fallback_for": "extension_request"},
        ],
        "total_cost_bdt": 0,
    },
    "naive_cost_bdt": 421.64,
}


def _evidence() -> list[dict]:
    out = []
    for i in range(41):
        late = i in (7, 19, 33)
        due = AS_OF + timedelta(days=-88 + i * 2)
        paid = due + timedelta(days=6 if late else -1)
        out.append({
            "invoice_no": f"INV-{3100 + i}",
            "supplier": f"Supplier {chr(65 + i % 23)}",
            "due_date": due.isoformat(),
            "paid_on": paid.isoformat(),
            "on_time": not late,
            "supplier_confirmed": True,
        })
    return out


PASSPORT = {
    "invoices_total": 41,
    "paid_on_time": 38,
    "confirmed_share": 1.0,
    "theta_mean": 0.907,
    "theta_low_5pct": 0.826,
    "default_probability": 0.030,
    "score": 0.507,
    "advance_rate_pct": 75.2,
    "partner_share_pct": 54.4,
    "evidence": _evidence(),
}

ACTIONS = [{
    "id": "act-1",
    "kind": "return_claim",
    "status": "proposed",
    "payload": {"summary": "Return Omeprazole (OM2409) and Cetirizine (CT2411) to Suppliers B and C", "amount": 9200},
    "proposed_by": "agent",
    "created_at": ts("08:05:00"),
    "decided_at": None,
    "result": None,
}]

LENDERS = [
    {"id": "wallet-lender", "name": "Wallet Lender", "kind": "mobile_wallet", "products": [
        {"key": "wallet_loan", "label": "Mobile-wallet loan", "apr_pct": 9, "fee_pct": None,
         "min_amount": 500, "max_amount": 30000},
    ]},
    {"id": "partner-bank", "name": "Partner Bank", "kind": "bank", "products": [
        {"key": "bank_supplier_credit", "label": "Supplier credit", "apr_pct": None, "fee_pct": 1,
         "min_amount": 10000, "max_amount": 500000},
        {"key": "bank_sme_loan", "label": "Small-business loan", "apr_pct": 13, "fee_pct": None,
         "min_amount": 200000, "max_amount": 5000000},
    ]},
]

CONSENT = {"id": "cons-1", "lender_id": "wallet-lender", "scopes": ["passport", "accounts"], "granted_at": ts("08:20:00")}

APPLICATION = {
    "id": "APP-0001",
    "pharmacy_id": PID,
    "pharmacy_name": "Green Life Pharmacy",
    "lender_id": "wallet-lender",
    "product_key": "wallet_loan",
    "amount": 8200,
    "status": "pending",
    "passport": PASSPORT,
    "decision": None,
    "created_at": ts("08:25:00"),
}

APPLICATION_DECIDED = {
    **APPLICATION,
    "status": "approved",
    "decision": {"approved": True, "payout_ref": "SANDBOX-WALLET-20261016-1",
                 "reason": "Default probability 0.030 is within the 0.05 limit and the amount is within limits."},
}

LOGS = [
    {"id": "lg-1", "ts": ts("08:00:00"), "tier": "T2", "component": "FORECAST", "event": "shortfall_detected",
     "data": {"date": d(10), "amount": 19000}},
    {"id": "lg-2", "ts": ts("08:00:01"), "tier": "T2", "component": "EXPIRY", "event": "batches_at_risk",
     "data": {"batches": 6, "value": 18400}},
    {"id": "lg-3", "ts": ts("08:05:00"), "tier": "T1", "component": "COPILOT", "event": "action_proposed",
     "data": {"action": "act-1", "kind": "return_claim"}},
]

CAPTURE_INVOICE = {
    "id": "cap-demo",
    "kind": "invoice",
    "status": "needs_review",
    "image_url": None,
    "extraction": {
        "kind": "invoice",
        "invoice": {
            "supplier_name": "Supplier K",
            "invoice_no": "K-77310",
            "invoice_date": d(0),
            "due_date": d(14),
            "total": 7500,
            "lines": [
                {"product": "Paracetamol 500 mg", "strength": "500 mg", "pack": "box of 100", "batch_no": "PC2510",
                 "expiry_date": "2028-03-31", "qty": 10, "unit_cost": 300, "line_total": 3000},
                {"product": "Cetirizine 10 mg", "strength": "10 mg", "pack": "box of 100", "batch_no": "CT2507",
                 "expiry_date": "2027-11-30", "qty": 15, "unit_cost": 200, "line_total": 3000},
                {"product": "Oral saline", "strength": None, "pack": "box of 25", "batch_no": "OR2506",
                 "expiry_date": "2027-06-30", "qty": 5, "unit_cost": 270, "line_total": 1350},
            ],
        },
        "sales_page": None,
        "field_confidence": {"invoice.lines[2].unit_cost": 0.3, "invoice.lines[2].qty": 0.5, "invoice.due_date": 0.5},
        "checks": [
            {"name": "Line totals", "passed": True, "detail": "Each line's quantity × price matches its line total."},
            {"name": "Invoice total", "passed": False,
             "detail": "Lines add up to BDT 7,350 but the invoice says BDT 7,500. The Oral saline price may be 300, not 270."},
            {"name": "Dates", "passed": True, "detail": "Expiry dates are after the invoice date."},
        ],
        "suspicious_text": [],
        "model": "gpt-6-luna",
        "prompt_version": "extraction_v1",
        "mode": "replay",
    },
}

# Endpoint name -> example, written to contracts/examples/<name>.json.
ALL = {
    "health": {"status": "ok"},
    "pharmacy": PHARMACY,
    "accounts": ACCOUNTS,
    "dues": DUES,
    "forecast": FORECAST,
    "alerts": ALERTS,
    "expiry": EXPIRY,
    "orders": ORDERS,
    "trim": TRIM,
    "funding_plan": FUNDING_PLAN,
    "passport": PASSPORT,
    "actions": ACTIONS,
    "lenders": LENDERS,
    "consent": CONSENT,
    "application": APPLICATION,
    "application_decided": APPLICATION_DECIDED,
    "logs": LOGS,
    "capture_invoice": CAPTURE_INVOICE,
}

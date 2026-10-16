"""Fallback extraction draft for POST /captures until app.agents.extraction exists.

Also served at GET /captures/cap-demo for the frontend's sample review screen.
"""

from datetime import date, timedelta

AS_OF = date(2026, 10, 16)


def d(offset: int) -> str:
    return (AS_OF + timedelta(days=offset)).isoformat()


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

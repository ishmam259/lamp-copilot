"""Load seed/green_life.json, and apply confirmed captures (invoices, sales pages)."""

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT

from . import models as m

SEED_DIR = REPO_ROOT / "seed"
DEMO_CAPTURES = ["invoice_supplier_f", "invoice_supplier_h", "sales_page"]


def _d(s: str | date) -> date:
    return s if isinstance(s, date) else date.fromisoformat(s)


def _supplier(db: Session, pid: str, name: str) -> m.Supplier:
    sup = db.scalar(select(m.Supplier).where(m.Supplier.pharmacy_id == pid, m.Supplier.name == name))
    if sup is None:  # first invoice from a new supplier
        sup = m.Supplier(pharmacy_id=pid, name=name, verified=False, return_cutoff_days=30)
        db.add(sup)
        db.flush()
    return sup


def add_invoice(db: Session, pid: str, inv: dict, *, supplier_confirmed: bool,
                capture_id: str | None = None, payment: dict | None = None, add_stock: bool = False) -> m.Invoice:
    """Insert an invoice with its lines. `inv` uses ExtractionResult.invoice field names
    (supplier_name or supplier). With add_stock, each line also becomes a stock batch."""
    sup = _supplier(db, pid, inv.get("supplier_name") or inv["supplier"])
    row = m.Invoice(
        pharmacy_id=pid, supplier_id=sup.id, invoice_no=inv["invoice_no"],
        invoice_date=_d(inv["invoice_date"]), due_date=_d(inv["due_date"]), total=inv["total"],
        status="paid" if payment else "unpaid", supplier_confirmed=supplier_confirmed, capture_id=capture_id,
        lines=[m.InvoiceLine(product=l["product"], strength=l.get("strength"), pack=l.get("pack"),
                             batch_no=l["batch_no"], expiry_date=_d(l["expiry_date"]), qty=l["qty"],
                             unit_cost=l["unit_cost"], line_total=l["line_total"]) for l in inv["lines"]],
    )
    if payment:
        row.payments.append(m.Payment(amount=payment["amount"], paid_on=_d(payment["paid_on"])))
    db.add(row)
    if add_stock:
        for l in inv["lines"]:
            db.add(m.StockBatch(pharmacy_id=pid, supplier_id=sup.id, product=l["product"], batch_no=l["batch_no"],
                                expiry_date=_d(l["expiry_date"]), qty=l["qty"], unit_cost=l["unit_cost"]))
    db.flush()
    return row


def upsert_sales_days(db: Session, pid: str, days: list[dict]) -> None:
    """A sales-book page replaces any existing rows for the same dates."""
    for day in days:
        dt = _d(day["date"])
        row = db.scalar(select(m.SalesDay).where(m.SalesDay.pharmacy_id == pid, m.SalesDay.date == dt))
        if row is None:
            row = m.SalesDay(pharmacy_id=pid, date=dt)
            db.add(row)
        for f in ("cash_sales", "credit_sales", "dues_collected", "expenses"):
            setattr(row, f, day[f])
    db.flush()


def apply_extraction(db: Session, pid: str, extraction: dict, capture_id: str | None = None) -> None:
    """Save a confirmed capture: an invoice (plus its stock) or a sales page."""
    if extraction.get("invoice"):
        add_invoice(db, pid, extraction["invoice"], supplier_confirmed=False, capture_id=capture_id, add_stock=True)
    if extraction.get("sales_page"):
        upsert_sales_days(db, pid, extraction["sales_page"]["days"])


def load_seed(db: Session, with_demo_captures: bool = False, path: Path | None = None) -> str:
    """Wipe every table and load the seed pharmacy. Returns the pharmacy id."""
    m.Base.metadata.drop_all(db.get_bind())
    m.Base.metadata.create_all(db.get_bind())
    seed = json.loads((path or SEED_DIR / "green_life.json").read_text(encoding="utf-8"))
    p = seed["pharmacy"]
    pid = p["id"]
    db.add(m.Pharmacy(id=pid, name=p["name"], city=p["city"], cash_on_hand=p["cash_on_hand"], settings=p["settings"]))
    for s in seed["suppliers"]:
        db.add(m.Supplier(pharmacy_id=pid, **s))
    db.flush()
    for inv in seed["invoices"]:
        add_invoice(db, pid, inv, supplier_confirmed=inv["supplier_confirmed"], payment=inv["payment"])
    upsert_sales_days(db, pid, seed["sales_days"])
    for e in seed["expense_schedule"]:
        db.add(m.ExpenseSchedule(pharmacy_id=pid, **e))
    for b in seed["stock_batches"]:
        sup = _supplier(db, pid, b["supplier"])
        db.add(m.StockBatch(pharmacy_id=pid, supplier_id=sup.id, product=b["product"], batch_no=b["batch_no"],
                            expiry_date=_d(b["expiry_date"]), qty=b["qty"], unit_cost=b["unit_cost"]))
    for pd in seed["patient_dues"]:
        db.add(m.PatientDue(pharmacy_id=pid, label=pd["label"], amount=pd["amount"], since=_d(pd["since"])))
    for o in seed["planned_orders"]:
        sup = _supplier(db, pid, o["supplier"])
        db.add(m.PlannedOrder(id=o["id"], pharmacy_id=pid, supplier_id=sup.id, ref=o["ref"],
                              due_date=_d(o["due_date"]), status=o["status"],
                              lines=[m.PlannedOrderLine(product=l["product"], qty=l["qty"], unit_cost=l["unit_cost"],
                                                        expiry_date=_d(l["expiry_date"])) for l in o["lines"]]))
    for lender in seed["lenders"]:
        db.add(m.Lender(id=lender["id"], name=lender["name"], kind=lender["kind"],
                        api_key_sha256=lender.get("api_key_sha256"),
                        products=[m.LenderProduct(**pr) for pr in lender["products"]]))
    db.flush()
    from app.engines.logbus import log

    log("T0", "DEV", "reset", db, pharmacy=pid, with_demo_captures=with_demo_captures)
    if with_demo_captures:
        for name in DEMO_CAPTURES:
            extraction = json.loads((SEED_DIR / "demo_captures" / f"{name}.json").read_text(encoding="utf-8"))
            apply_extraction(db, pid, extraction, capture_id=f"demo-{name}")
            log("T1", "CAPTURE", "capture_confirmed", db, capture=f"demo-{name}", kind=extraction["kind"])
    _log_detections(db, pid)
    db.commit()
    return pid


def _log_detections(db: Session, pid: str) -> None:
    """What the engines find in the fresh data, so the live log starts with it."""
    from app.engines import get_expiry, get_forecast
    from app.engines.logbus import log

    fc = get_forecast(db, pid)
    if fc.shortfalls:
        s = fc.shortfalls[0]
        log("T2", "FORECAST", "shortfall_detected", db, date=s.date, amount=s.amount, cause=s.cause)
    ex = get_expiry(db, pid)
    if ex.batches:
        log("T2", "EXPIRY", "batches_at_risk", db, batches=len(ex.batches), value=ex.at_risk_value,
            return_eligible=ex.return_eligible_value)

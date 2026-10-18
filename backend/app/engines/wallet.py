"""Sandbox wallet and statement reconciliation (win plan CORE-05).

Wallet: LaMP's own movements (loan payouts, credited when the lender decides; the
forecast already counts them through cash_on_hand). balance = cash_on_hand;
opening_balance = balance - Σ transactions.

Reconciliation: each statement line from the 30 days before as_of is matched to the books:
- a debit matches a recorded supplier payment with the same amount, a payee alias naming
  the same supplier, and a date within ±3 days → "matched";
- a debit that fits a payment already matched → "duplicate" (paid twice);
- a debit with no fitting payment → "unmatched";
- a recorded payment in the window with no statement line → "missing_from_statement";
- a credit matches a LaMP payout by its reference.
Matching is read-only; it never changes the books. Each problem gets a recommendation.
"""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import AccountOut

from .common import as_of, get_pharmacy, r2
from .logbus import log

WINDOW_DAYS = 30
DATE_TOLERANCE_DAYS = 3


def record_payout(db: Session, pid: str, amount: float, ref: str, on) -> None:
    """Credit a lender payout to the sandbox wallet."""
    n = (db.scalar(select(func.count()).select_from(m.WalletTxn)) or 0) + 1
    db.add(m.WalletTxn(id=f"wt-{n}", pharmacy_id=pid, date=on, amount=amount, kind="loan_payout", ref=ref,
                       created_at=datetime.now(timezone.utc).replace(tzinfo=None)))
    db.flush()
    log("T3", "WALLET", "wallet_credited", db, amount=amount, ref=ref)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def get_account(db: Session, pid: str) -> AccountOut:
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    txns = list(db.scalars(select(m.WalletTxn).where(m.WalletTxn.pharmacy_id == pid).order_by(m.WalletTxn.id)))
    balance = ph.cash_on_hand
    opening = balance - sum(t.amount for t in txns)

    start = today - timedelta(days=WINDOW_DAYS)
    payments = list(db.execute(
        select(m.Payment, m.Invoice, m.Supplier).join(m.Invoice, m.Payment.invoice_id == m.Invoice.id)
        .join(m.Supplier, m.Invoice.supplier_id == m.Supplier.id)
        .where(m.Invoice.pharmacy_id == pid, m.Payment.paid_on >= start, m.Payment.paid_on < today)
        .order_by(m.Payment.paid_on, m.Payment.id)))
    lines = list(db.scalars(select(m.StatementLine).where(m.StatementLine.pharmacy_id == pid)
                            .order_by(m.StatementLine.date, m.StatementLine.id)))
    used: set[int] = set()
    matches = []
    for line in lines:
        base = {"ref": line.ref, "date": line.date, "amount": line.amount, "payee": line.payee}
        if line.amount > 0:
            continue
        fits = [(p, inv, sup) for p, inv, sup in payments
                if abs(p.amount - (-line.amount)) < 0.005 and _norm(sup.name) in _norm(line.payee)
                and abs((p.paid_on - line.date).days) <= DATE_TOLERANCE_DAYS]
        free = [f for f in fits if f[0].id not in used]
        if free:
            p, inv, sup = free[0]
            used.add(p.id)
            matches.append({**base, "status": "matched", "invoice_no": inv.invoice_no, "supplier": sup.name,
                            "note": f"Payment for {inv.invoice_no}."})
        elif fits:
            p, inv, sup = fits[0]
            matches.append({**base, "status": "duplicate", "invoice_no": inv.invoice_no, "supplier": sup.name,
                            "note": f"{inv.invoice_no} was already paid on {fits[0][0].paid_on:%d %b}: "
                                    f"this looks like a second payment."})
        else:
            matches.append({**base, "status": "unmatched", "note": "No bill in the books matches this payment."})
    for p, inv, sup in payments:
        if p.id not in used:
            matches.append({"ref": inv.invoice_no, "date": p.paid_on, "amount": -p.amount, "payee": sup.name,
                            "status": "missing_from_statement", "invoice_no": inv.invoice_no, "supplier": sup.name,
                            "note": "Recorded as paid, but no such payment is on the statement."})
    for t in txns:
        matches.append({"ref": t.ref, "date": t.date, "amount": t.amount, "payee": "Loan payout",
                        "status": "matched", "note": "Sandbox loan payout credited to the wallet."})

    counts = {k: sum(1 for x in matches if x["status"] == k)
              for k in ("matched", "duplicate", "unmatched", "missing_from_statement")}
    recs = []
    for x in matches:
        if x["status"] == "duplicate":
            recs.append(f"Ask {x['supplier']} to refund or credit BDT {-x['amount']:,.0f} paid twice for {x['invoice_no']}.")
        elif x["status"] == "unmatched":
            recs.append(f"Check the BDT {-x['amount']:,.0f} payment to {x['payee']} on {x['date']:%d %b}: "
                        "add the bill if it was a business expense.")
        elif x["status"] == "missing_from_statement":
            recs.append(f"{x['invoice_no']} ({x['supplier']}) is marked paid but the money never left: "
                        "confirm with the supplier before they chase it.")
    return AccountOut(opening_balance=r2(opening), balance=r2(balance),
                      transactions=[{"date": t.date, "amount": t.amount, "kind": t.kind, "ref": t.ref} for t in txns],
                      matches=matches, counts=counts, recommendations=recs)

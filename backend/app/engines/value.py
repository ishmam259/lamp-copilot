"""Value ledger (win plan CORE-10): what the owner's approved actions saved or recovered,
each with its basis and its counterfactual. Engine numbers only.

- return_claim executed → expected supplier credit (9,200). Without it: the stock
  expires on the shelf and is written off.
- trim_order executed → old_total − new_total (10,800): stock not bought that wouldn't
  have sold before expiry.
- the interest the trim avoided: that saving no longer had to be borrowed, so
  saving × wallet APR × tenor / 365 (10,800 × 9% × 90/365 = 239.67). Equivalently the
  naive loan for the untrimmed shortfall (421.64) minus the plan's loan (181.97).
- extension accepted by the supplier → the plan's fallback loan was never needed: its
  interest (8,200 × 9% × 90/365 = 181.97) is avoided.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import ValueOut

from .common import get_pharmacy, r2


def _wallet_cost(db: Session, amount: float) -> tuple[float, float, int]:
    w = db.scalar(select(m.LenderProduct).where(m.LenderProduct.key == "wallet_loan"))
    return amount * w.apr_pct / 100 * w.tenor_days / 365, w.apr_pct, w.tenor_days


def get_value(db: Session, pid: str) -> ValueOut:
    get_pharmacy(db, pid)
    done = list(db.scalars(select(m.Action).where(m.Action.pharmacy_id == pid, m.Action.status == "executed")
                           .order_by(m.Action.created_at, m.Action.id)))
    items = []
    for a in done:
        r = a.result or {}
        if a.kind == "return_claim":
            items.append({"action_id": a.id, "kind": a.kind, "label": f"Return claim {r.get('claim_id')}",
                          "amount": r2(r.get("expected_credit", 0)),
                          "basis": "Expected supplier credit for the return-eligible expiring batches.",
                          "counterfactual": "The stock expires on the shelf and is written off."})
        elif a.kind == "trim_order":
            saving = r2(r.get("old_total", 0) - r.get("new_total", 0))
            items.append({"action_id": a.id, "kind": a.kind, "label": "Smaller order",
                          "amount": saving,
                          "basis": f"Order {r.get('old_total', 0):,.0f} → {r.get('new_total', 0):,.0f}: stock that "
                                   "wouldn't sell before expiry not bought.",
                          "counterfactual": "Bought, then expired unsold."})
            if saving > 0:
                cost, apr, tenor = _wallet_cost(db, saving)
                items.append({"action_id": a.id, "kind": "interest_avoided", "label": "Interest avoided by the trim",
                              "amount": r2(cost),
                              "basis": f"{saving:,.0f} no longer borrowed: at {apr:g}% a year for {tenor} days.",
                              "counterfactual": "Borrow the full shortfall with the wallet loan."})
        elif a.kind == "extension_request" and r.get("status") == "accepted":
            amount = float(a.payload.get("amount") or 0)
            cost, apr, tenor = _wallet_cost(db, amount)
            items.append({"action_id": a.id, "kind": "interest_avoided", "label": "Supplier extension accepted",
                          "amount": r2(cost),
                          "basis": f"The backup loan of {amount:,.0f} wasn't needed: at {apr:g}% a year for {tenor} days.",
                          "counterfactual": "Take the backup wallet loan."})
    return ValueOut(items=items, total=r2(sum(i["amount"] for i in items)))

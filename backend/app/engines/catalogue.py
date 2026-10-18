"""Financing catalogue (win plan CORE-14): sourced Bangladeshi product archetypes matched
to the pharmacy's need.

Terms come from seed/financing_catalogue.json, each with its published source and date;
they are never tuned to protect the demo plan. For the need (default: the funding plan's,
8,200 by 26 Oct), each archetype is checked:
- amount within its published limits (limits the source doesn't state don't block);
- speed: it must pay out before needed_by (days until then vs its speed_days);
- requirements LaMP can't verify for this supplier (wallet merchant, platform member) make
  it ineligible; ones the owner can confirm (trade licence, clean CIB record, MFI
  membership) are listed in `to_confirm`;
- no published price → not comparable, so ineligible.
Cost is compared over one horizon, HORIZON_DAYS (the wallet loan's 90 days), as simple
interest: amount × APR × min(tenor, horizon) / 365, or 0 inside an interest-free window
shorter than the need. plan_holds says whether the funding plan's fallback is still the
cheapest eligible certain option; if not, the team decides (win plan D-07).
"""

import json
from datetime import date

from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.schemas import CatalogueOut, FundingNeed

from .common import as_of, get_pharmacy, r2
from .funding import get_funding_plan

CATALOGUE = REPO_ROOT / "seed" / "financing_catalogue.json"
HORIZON_DAYS = 90
BLOCKING = {"supplier_is_wallet_merchant": "the supplier isn't known to take wallet merchant payments",
            "supplier_on_platform": "the supplier isn't known to sell through this platform"}
CONFIRM = {"trade_licence": "a trade licence", "clean_cib": "a clean CIB credit record",
           "mfi_membership": "membership of the microfinance institution"}
PURPOSE_NOTE = {"personal": "A retail loan to the owner personally: check it may be used for a business bill.",
                "merchant_purchase": "Only for purchases at wallet merchants.",
                "business": "A business loan."}


def _load() -> list[dict]:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))["archetypes"]


def get_catalogue(db: Session, pid: str, need: FundingNeed | None = None) -> CatalogueOut:
    plan = get_funding_plan(db, pid, need)
    need = plan.need
    today = as_of(get_pharmacy(db, pid))
    days_left = (need.needed_by - today).days
    fallback = next((o.cost_bdt for o in plan.options if o.key == "wallet_loan"), None)

    out = []
    for a in _load():
        reasons, confirm = [], [CONFIRM[r] for r in a["requires"] if r in CONFIRM]
        if a["min_amount"] is not None and need.amount < a["min_amount"]:
            reasons.append(f"minimum is BDT {a['min_amount']:,.0f}")
        if a["max_amount"] is not None and need.amount > a["max_amount"]:
            reasons.append(f"maximum is BDT {a['max_amount']:,.0f}")
        if a["speed_days"] > days_left:
            reasons.append(f"takes about {a['speed_days']} days; the money is needed in {days_left}")
        reasons += [BLOCKING[r] for r in a["requires"] if r in BLOCKING]
        cost = None
        if a["apr_pct"] is None:
            reasons.append("its price isn't published, so it can't be compared")
        else:
            days = min(a["tenor_days"] or HORIZON_DAYS, HORIZON_DAYS)
            free = a.get("interest_free_days") or 0
            cost = 0.0 if free >= HORIZON_DAYS else need.amount * a["apr_pct"] / 100 * days / 365
        out.append({
            "key": a["key"], "label": a["label"], "provider_type": a["provider_type"],
            "anchored_on": a["anchored_on"], "source": a["source"],
            "source_date": date.fromisoformat(a["source_date"]) if a["source_date"] else None,
            "permitted_purpose": a["permitted_purpose"], "apr_pct": a["apr_pct"],
            "amount_financed": need.amount if cost is not None else None, "tenor_days": a["tenor_days"],
            "horizon_days": HORIZON_DAYS, "cost_of_gap_bdt": r2(cost) if cost is not None else None,
            "cost_of_gap_pct_of_need": round(cost / need.amount * 100, 2) if cost is not None and need.amount else None,
            "speed_days": a["speed_days"], "eligible": not reasons,
            "ineligible_reason": "; ".join(reasons).capitalize() + "." if reasons else None,
            "to_confirm": confirm, "note": f"{PURPOSE_NOTE[a['permitted_purpose']]} {a['terms_note']}",
        })
    out.sort(key=lambda o: (not o["eligible"], o["cost_of_gap_bdt"] is None, o["cost_of_gap_bdt"] or 0))
    eligible = [o for o in out if o["eligible"]]
    cheapest = min((o["cost_of_gap_bdt"] for o in eligible), default=None)
    holds = cheapest is None or fallback is None or cheapest >= fallback - 0.005
    return CatalogueOut(need=need, horizon_days=HORIZON_DAYS, matched=len(out), eligible=len(eligible), options=out,
                        cheapest_eligible_cost_bdt=cheapest, plan_fallback_cost_bdt=fallback, plan_holds=holds)

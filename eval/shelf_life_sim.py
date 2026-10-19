"""Shelf-life credit simulation (PROOF-04, and the simulation half of PROOF-05).

Runs N perturbed copies of the seed pharmacy (Green Life, with its demo captures) through the
real engines and compares two lenders on the first shortfall:

- purpose-blind: finances the whole untrimmed shortfall; the order goes ahead as planned.
- shelf-life credit (engines/passport.get_shelf_life_credit): does not finance stock that won't
  sell before expiry; the owner trims the order to the sellable quantity (engines/expiry.get_trim).

Per shop it perturbs, from one published seed:
  cash on hand ×U(0.6, 1.4); daily sales ×U(0.8, 1.2); purchase history per product ×U(0.6, 1.4)
  (which sets the engine's sales rates); each planned-order line qty ×U(0.5, 1.8) and expiry
  shifted by U(−30, +150) days.
Actual sales then differ from the engine's estimate: the true rate is the estimated rate
× lognormal(0, 0.25), so "expires unsold" is measured against sales the engine didn't see.

Measured per lender: financed amount; financed stock that expires unsold (the unsold value
at expiry, capped at the amount financed); interest (wallet loan, 9% APR, 90 days); need left
unfinanced after the trim (shelf-life only; the purpose-blind lender finances it all); and
(PROOF-05) the 30-day expiry write-off and days short. Synthetic data, labelled as such.

    python eval/shelf_life_sim.py            # 200 shops, seed 2026 -> eval/shelf_life_sim.md/.json
    python eval/shelf_life_sim.py --n 50 --seed 7
"""

import argparse
import json
import math
import os
import random
import statistics
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DEV_MODE", "true")
os.environ["BREVO_API_KEY"] = ""

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import models as m  # noqa: E402
from app.db.seed import load_seed  # noqa: E402
from app.engines.common import as_of  # noqa: E402
from app.engines.expiry import get_trim, sales_rates  # noqa: E402
from app.engines.forecast import get_forecast  # noqa: E402
from app.engines.passport import get_shelf_life_credit  # noqa: E402

WALLET_APR, WALLET_DAYS = 9.0, 90
SALES_NOISE_SIGMA = 0.25


def interest(amount: float) -> float:
    return amount * WALLET_APR / 100 * WALLET_DAYS / 365


def perturb(db, pid: str, rng: random.Random) -> None:
    ph = db.get(m.Pharmacy, pid)
    today = as_of(ph)
    ph.cash_on_hand = round(ph.cash_on_hand * rng.uniform(0.6, 1.4))
    for d in db.scalars(select(m.SalesDay).where(m.SalesDay.pharmacy_id == pid)):
        f = rng.uniform(0.8, 1.2)
        d.cash_sales, d.credit_sales = round(d.cash_sales * f), round(d.credit_sales * f)
    factors: dict[str, float] = {}
    for line in db.scalars(select(m.InvoiceLine).join(m.Invoice).where(m.Invoice.pharmacy_id == pid)):
        f = factors.setdefault(line.product, rng.uniform(0.6, 1.4))
        line.qty = max(1, round(line.qty * f))
    for line in db.scalars(select(m.PlannedOrderLine).join(m.PlannedOrder).where(m.PlannedOrder.pharmacy_id == pid)):
        line.qty = max(1, round(line.qty * rng.uniform(0.5, 1.8)))
        line.expiry_date = max(today + timedelta(days=1), line.expiry_date + timedelta(days=rng.randint(-30, 150)))
    db.flush()


def unsold_value(lines, qty_of, true_rates, today, buffer_days) -> float:
    """Cost value of order stock still unsold when shops stop selling it (buffer days before expiry)."""
    total = 0.0
    for line in lines:
        days = max(0, (line.expiry_date - today).days - buffer_days)
        sold = min(qty_of(line), true_rates.get(line.product, 0) * days)
        total += (qty_of(line) - sold) * line.unit_cost
    return total


def days_short(fc) -> int:
    return sum(1 for d in fc.days if d.balance < 0)


def one_shop(db, pid: str, rng: random.Random) -> dict | None:
    perturb(db, pid, rng)
    ph = db.get(m.Pharmacy, pid)
    today, buffer_days = as_of(ph), ph.settings["expiry_buffer_days"]
    credit = get_shelf_life_credit(db, pid)
    need = credit.counterfactual_purpose_blind
    if need <= 0 or not credit.order_id:
        return None
    order = db.get(m.PlannedOrder, credit.order_id)
    trim = {t.product: t.suggested_qty for t in get_trim(db, pid, order.id).lines}
    est = sales_rates(db, pid, today)
    true_rates = {p: r * math.exp(rng.gauss(0, SALES_NOISE_SIGMA)) for p, r in est.items()}

    unsold_blind = unsold_value(order.lines, lambda l: l.qty, true_rates, today, buffer_days)
    unsold_slc = unsold_value(order.lines, lambda l: trim[l.product], true_rates, today, buffer_days)
    trimmed_total = sum(trim[l.product] * l.unit_cost for l in order.lines)
    fc_blind = get_forecast(db, pid)
    fc_trim = get_forecast(db, pid, order_totals={order.id: trimmed_total})
    need_after_trim = next((s.amount for s in fc_trim.shortfalls if s.date == credit.needed_by), 0.0)
    financed_slc = credit.financeable
    return {
        "need": need, "not_financed": credit.not_financed, "changed": credit.not_financed > 0,
        "financed": {"blind": need, "slc": financed_slc},
        "financed_unsold": {"blind": min(need, unsold_blind), "slc": min(financed_slc, unsold_slc)},
        "interest": {"blind": interest(need), "slc": interest(financed_slc)},
        "unfinanced": {"blind": 0.0, "slc": max(0.0, need_after_trim - financed_slc)},
        "expiry_loss": {"blind": unsold_blind, "slc": unsold_slc},
        # days short before any financing arrives: what the owner faces if the loan is late
        "days_short": {"blind": days_short(fc_blind), "slc": days_short(fc_trim)},
    }


def pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def summary(rows: list[dict], key: str) -> dict:
    out = {}
    for lender in ("blind", "slc"):
        xs = [r[key][lender] for r in rows]
        out[lender] = {"median": round(statistics.median(xs), 2), "p10": round(pct(xs, 0.1), 2),
                       "p90": round(pct(xs, 0.9), 2), "mean": round(statistics.fmean(xs), 2)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Shelf-life credit simulation (PROOF-04)")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=str(ROOT / "eval" / "shelf_life_sim"))
    a = ap.parse_args()

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    rng = random.Random(a.seed)

    with Session() as db:  # the unperturbed seed must reproduce the golden card
        pid = load_seed(db, with_demo_captures=True)
        g = get_shelf_life_credit(db, pid)
        golden = (g.counterfactual_purpose_blind, g.not_financed, g.financeable)
        assert golden == (19000, 10800, 8200), golden

    rows, skipped = [], 0
    for _ in range(a.n):
        with Session() as db:
            pid = load_seed(db, with_demo_captures=True)
            r = one_shop(db, pid, rng)
            db.rollback()
        if r is None:
            skipped += 1
        else:
            rows.append(r)

    keys = ("financed", "financed_unsold", "interest", "unfinanced", "expiry_loss", "days_short")
    result = {"n": a.n, "seed": a.seed, "with_shortfall": len(rows), "no_shortfall": skipped,
              "changed_share": round(sum(r["changed"] for r in rows) / len(rows), 3) if rows else 0,
              "golden_check": list(golden), "sales_noise_sigma": SALES_NOISE_SIGMA,
              "summary": {k: summary(rows, k) for k in keys}}
    Path(a.out + ".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    Path(a.out + ".md").write_text(report(result), encoding="utf-8")
    print(Path(a.out + ".md").read_text(encoding="utf-8").encode("ascii", "replace").decode())


LABELS = {
    "financed": "Amount financed (BDT)",
    "financed_unsold": "Financed stock that expires unsold (BDT)",
    "interest": "Interest, wallet loan 9% APR 90 days (BDT)",
    "unfinanced": "Need left unfinanced after the trim (BDT)",
    "expiry_loss": "Order stock written off at expiry (BDT)",
    "days_short": "Days with negative cash in the 30-day forecast",
}


def report(r: dict) -> str:
    f = lambda s: f"{s['median']:,.0f} ({s['p10']:,.0f}–{s['p90']:,.0f})"  # noqa: E731
    lines = [
        "# Shelf-life credit simulation (synthetic)",
        "",
        f"**{r['n']} perturbed pharmacies, seed {r['seed']}**, run through the real engines "
        "(`python eval/shelf_life_sim.py`). Synthetic: every shop is a perturbed copy of the seed "
        "pharmacy, Green Life, not a real shop.",
        "",
        f"- {r['with_shortfall']} shops have a shortfall to finance; {r['no_shortfall']} have none and are left out.",
        f"- **The financed amount changes in {r['changed_share']:.0%} of shops**: shelf-life credit finances less "
        "than the purpose-blind lender because part of the order won't sell before expiry.",
        f"- The unperturbed seed reproduces the golden card: {r['golden_check'][0]:,.0f} / "
        f"{r['golden_check'][1]:,.0f} / {r['golden_check'][2]:,.0f}.",
        "",
        "Median (P10–P90) per shop:",
        "",
        "| Measure | Purpose-blind lender | Shelf-life credit |",
        "|---|---|---|",
    ]
    for k, label in LABELS.items():
        s = r["summary"][k]
        lines.append(f"| {label} | {f(s['blind'])} | {f(s['slc'])} |")
    lines += [
        "",
        "## Assumptions",
        "",
        "- Purpose-blind: finances the whole untrimmed first shortfall; the order goes ahead as planned.",
        "- Shelf-life credit: finances `need − stock that won't sell before expiry` (engines/passport.py); "
        "the owner trims the order to the sellable quantity (engines/expiry.py, 30-day selling buffer).",
        "- Perturbations: cash ×U(0.6, 1.4); daily sales ×U(0.8, 1.2); purchase history per product "
        "×U(0.6, 1.4); order line qty ×U(0.5, 1.8); line expiry shifted U(−30, +150) days.",
        f"- Actual sales differ from the engine's estimate: true rate = estimated rate × lognormal(0, "
        f"{r['sales_noise_sigma']}). \"Expires unsold\" and the write-off are measured against those actual sales.",
        "- Financed stock that expires unsold = unsold value at expiry, capped at the amount financed.",
        "- Interest uses the seed's wallet loan (9% APR, 90 days) for both lenders.",
        "- Need left unfinanced = the trimmed order's shortfall on the same date minus what shelf-life credit "
        "finances. The purpose-blind lender finances everything, so 0. For shelf-life credit it is 0 by "
        "construction: the trim saves at least as much as the credit withholds.",
        "- Days short counts days below zero in the 30-day forecast before any financing arrives. Most come "
        "from later bills (rent, other suppliers), so the trim moves it little.",
        "- Not measured: the cash forecast's error on actual sales. In a simulation the \"actual\" sales are "
        "the noise we inject, so the number would only restate the noise; it needs real daily sales.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()

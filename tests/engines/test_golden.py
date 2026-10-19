"""Every F2 golden number in docs/PLAN.md section 6, from seed + demo captures."""

from datetime import date

from app.engines import (
    get_accounts, get_alerts, get_dues, get_expiry, get_forecast, get_funding_plan, get_passport, get_trim,
)

PID = "green-life"
AS_OF = date(2026, 10, 16)


def test_accounts(db):
    a = get_accounts(db, PID)
    assert a.sales == 412_500
    assert a.gross_margin_pct == 12 and a.gross_profit == 49_500
    assert a.overheads == 36_000 and a.net_profit == 13_500
    assert a.stock_value == 210_000 and a.stock_days == 17.4
    assert a.patient_dues == 38_000 and a.patient_due_days == 2.8
    assert a.active_suppliers == 23
    assert a.expiring_value_60d == 18_400
    assert a.top_suppliers[0].name == "Supplier A"
    mon = next(s for s in a.slow_movers if s.product.startswith("Montelukast") and s.qty == 30)
    assert (mon.sellable_qty, mon.at_risk_value) == (12, 10_800)


def test_forecast_shortfall(db):
    f = get_forecast(db, PID)
    assert len(f.days) == 30 and f.days[0].date == AS_OF
    first = f.shortfalls[0]
    assert first.date == date(2026, 10, 26)
    assert first.amount == 19_000
    assert first.cause == "Supplier A order BDT 60,000"
    assert f.days[9].balance == 41_000  # closing balance the day before the 60,000 order
    assert f.days[10].items[0].amount == -60_000


def test_dues_calendar(db):
    dues = get_dues(db, PID)
    assert [(i.invoice_no, i.status) for i in dues.items] == [
        ("D-20931", "due_soon"), ("F-1182", "due_soon"), ("PO-A-1026", "upcoming"), ("H-5520", "upcoming")]
    assert dues.total_due == 85_950


def test_alerts(db):
    alerts = {a.kind: a for a in get_alerts(db, PID)}
    assert alerts["shortfall"].title == "Short BDT 19,000 on 26 Oct"
    assert "BDT 41,000" in alerts["shortfall"].detail
    assert alerts["return_window"].title == "Claim returns worth BDT 9,200"
    assert alerts["expiry"].title == "BDT 18,400 of stock expires within 60 days"
    assert "patient_dues" in alerts and "suspicious_document" not in alerts


def test_expiry(db):
    e = get_expiry(db, PID)
    assert len(e.batches) == 6
    assert e.at_risk_value == 18_400 and e.return_eligible_value == 9_200
    assert {b.batch_no for b in e.batches if b.return_eligible} == {"OM2409", "CT2411"}


def test_trim(db):
    t = get_trim(db, PID, "o-1")
    mon = t.lines[0]
    assert mon.product.startswith("Montelukast")
    assert (mon.qty, mon.sales_rate_per_day, mon.sellable_days, mon.sellable_qty) == (30, 0.2, 60, 12)
    assert (mon.suggested_qty, mon.at_risk_value) == (12, 10_800)
    assert all(l.suggested_qty == l.qty for l in t.lines[1:])
    assert (t.original_total, t.suggested_total, t.saving) == (60_000, 49_200, 10_800)


def test_passport(db):
    p = get_passport(db, PID)
    assert (p.invoices_total, p.paid_on_time, p.confirmed_share) == (41, 38, 1.0)
    assert (p.theta_low_5pct, p.default_probability, p.score) == (0.826, 0.030, 0.507)
    assert (p.advance_rate_pct, p.partner_share_pct) == (75.2, 54.4)
    assert len(p.evidence) == 41 and sum(not e.on_time for e in p.evidence) == 3


def test_funding_plan(db):
    f = get_funding_plan(db, PID)
    assert (f.need.amount, f.need.needed_by) == (8_200, date(2026, 10, 26))
    o = {x.key: x for x in f.options}
    assert o["trim_order"].amount == 10_800 and o["trim_order"].cost_bdt == 0
    assert o["return_claims"].amount == 9_200
    assert o["supplier_extension"].eligible and o["supplier_extension"].certainty == "uncertain"
    assert o["wallet_loan"].cost_bdt == 181.97
    assert o["bank_supplier_credit"].cost_bdt == 492.00 and o["bank_supplier_credit"].amount == 49_200
    assert not o["bank_sme_loan"].eligible and "200,000" in o["bank_sme_loan"].reason
    steps = [(s.action_kind, s.amount, s.when, s.fallback_for) for s in f.plan.steps]
    assert steps == [
        ("trim_order", 10_800, AS_OF, None),
        ("extension_request", 8_200, AS_OF, None),
        ("loan_application", 8_200, date(2026, 10, 22), "extension_request"),
    ]
    assert f.plan.total_cost_bdt == 0
    assert f.naive_cost_bdt == 421.64


def test_cost_disclosure(db):
    """Win plan CORE-15: APR on the amount financed, tenor, and the cost of this gap."""
    o = {x.key: x for x in get_funding_plan(db, PID).options}
    w, b = o["wallet_loan"], o["bank_supplier_credit"]
    assert (w.apr_pct, w.amount_financed, w.tenor_days, w.cost_of_gap_bdt, w.cost_of_gap_pct_of_need) ==         (9, 8_200, 90, 181.97, 2.22)
    assert (b.apr_pct, b.amount_financed, b.tenor_days, b.cost_of_gap_bdt, b.cost_of_gap_pct_of_need) ==         (12.2, 49_200, 30, 492.00, 6.0)
    ext = o["supplier_extension"]
    assert (ext.amount_financed, ext.tenor_days, ext.cost_of_gap_bdt) == (8_200, 20, 0)
    assert o["trim_order"].amount_financed is None and o["return_claims"].cost_of_gap_bdt is None
    assert o["bank_sme_loan"].cost_of_gap_bdt is None  # ineligible: no cost to disclose


def test_shelf_life_credit(db):
    """Win plan CORE-11: 19,000 purpose-blind → 10,800 not financed → 8,200 financeable."""
    from app.engines import get_shelf_life_credit

    s = get_shelf_life_credit(db, PID)
    assert (s.order_id, s.needed_by) == ("o-1", date(2026, 10, 26))
    assert (s.counterfactual_purpose_blind, s.not_financed, s.financeable) == (19_000, 10_800, 8_200)
    slow = [b for b in s.batches if b.unsellable_value > 0]
    assert [(b.qty_ordered, b.sellable_qty, b.unsellable_value) for b in slow] == [(30, 12, 10_800)]
    # the financeable amount is exactly the need left after the trim
    assert s.financeable == get_funding_plan(db, PID).need.amount

"""Every F2 golden number in docs/PLAN.md section 6, from seed + demo captures."""

from datetime import date

from app.engines import get_accounts, get_alerts, get_dues, get_expiry, get_forecast, get_trim

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
    day10 = f.days[10]
    assert day10.balance == -19_000  # 41,000 before the 60,000 order


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

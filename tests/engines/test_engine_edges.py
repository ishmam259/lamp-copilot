"""Edge cases for the F2 engines."""

from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.db import models as m
from app.engines import get_accounts, get_dues, get_forecast
from app.engines.dues import status_for
from app.engines.expiry import sellable_qty

PID = "green-life"


def test_seed_only_is_not_golden_until_captures(seed_only_db):
    a = get_accounts(seed_only_db, PID)
    assert a.stock_value == 192_500  # 17,500 arrives with the two demo invoices
    assert a.sales < 412_500         # three days arrive with the sales-book page


def test_zero_sales_gives_zero_days(db):
    db.query(m.SalesDay).delete()
    a = get_accounts(db, PID)
    assert (a.sales, a.stock_days, a.patient_due_days) == (0, 0, 0)


def test_no_history_forecast_is_flat_except_named(db):
    db.query(m.SalesDay).delete()
    f = get_forecast(db, PID)
    assert f.days[1].balance == f.days[0].balance  # no receipts, no restock, nothing due on day 1


def test_empty_orders_and_dues(db):
    db.query(m.PlannedOrderLine).delete()
    db.query(m.PlannedOrder).delete()
    for inv in db.query(m.Invoice):
        inv.status = "paid"
    d = get_dues(db, PID)
    assert d.items == [] and d.total_due == 0
    assert get_forecast(db, PID).shortfalls == []


def test_overdue_invoice_lands_on_day_zero(db):
    inv = db.query(m.Invoice).filter_by(invoice_no="D-20931").one()
    inv.due_date = date(2026, 10, 10)
    assert get_dues(db, PID).items[0].status == "overdue"
    assert any("D-20931" in i.label for i in get_forecast(db, PID).days[0].items)


def test_expired_batch_not_counted_as_expiring(db):
    b = db.query(m.StockBatch).filter_by(batch_no="VB2385").one()
    b.expiry_date = date(2026, 10, 1)
    assert get_accounts(db, PID).expiring_value_60d == 18_400 - 1_200


@pytest.mark.parametrize("left,status", [(-1, "overdue"), (0, "due_soon"), (7, "due_soon"), (8, "upcoming")])
def test_due_status(left, status):
    assert status_for(left) == status


def test_sellable_qty():
    assert sellable_qty(30, 0.2, 90, 30) == (60, 12)
    assert sellable_qty(10, 5, 20, 30) == (0, 0)   # inside the buffer: nothing sellable
    assert sellable_qty(10, 5, 400, 30) == (370, 10)


def test_unknown_pharmacy(db):
    with pytest.raises(HTTPException):
        get_accounts(db, "nope")

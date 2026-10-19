"""Current alerts, generated on request (not stored)."""

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as m
from app.schemas import Alert

from .common import as_of, get_pharmacy
from .expiry import claimed_batch_nos
from .forecast import get_forecast


def _bdt(x: float) -> str:
    return f"BDT {x:,.0f}"


def get_alerts(db: Session, pid: str) -> list[Alert]:
    """Rules:
    - shortfall: the first forecast shortfall (critical)
    - return_window: return-eligible batches (days_left >= supplier.return_cutoff_days)
      whose cutoff is at most 14 days away (warning)
    - expiry: batches expiring within 60 days (warning)
    - patient_dues: any patient due older than 30 days (info)
    - suspicious_document: any capture whose extraction has suspicious_text (critical)
    created_at is as_of at 08:00 UTC, so output is deterministic.
    """
    ph = get_pharmacy(db, pid)
    today = as_of(ph)
    stamp = datetime.combine(today, time(8, 0), tzinfo=timezone.utc)
    alerts: list[dict] = []

    def add(kind, severity, title, detail):
        alerts.append({"id": f"al-{len(alerts) + 1}", "kind": kind, "severity": severity,
                       "title": title, "detail": detail, "created_at": stamp})

    fc = get_forecast(db, pid)
    if fc.shortfalls:
        s = fc.shortfalls[0]
        i = next(n for n, x in enumerate(fc.days) if x.date == s.date)
        before = fc.days[i - 1].balance if i else fc.start_cash  # payments go out at the start of the day
        add("shortfall", "critical", f"Short {_bdt(s.amount)} on {s.date:%d %b}",
            f"{s.cause} is due. Forecast cash that day is {_bdt(before)}.")

    batches = list(db.scalars(select(m.StockBatch).where(m.StockBatch.pharmacy_id == pid)))
    expiring = [b for b in batches if 0 <= (b.expiry_date - today).days <= 60]
    claimed = claimed_batch_nos(db, pid)
    window = [b for b in expiring if 0 <= (b.expiry_date - today).days - b.supplier.return_cutoff_days <= 14
              and b.batch_no not in claimed]
    if window:
        add("return_window", "warning", f"Claim returns worth {_bdt(sum(b.qty * b.unit_cost for b in window))}",
            f"{len(window)} batches can still go back to their suppliers before the return window closes.")
    if expiring:
        past = sum(1 for b in expiring if (b.expiry_date - today).days < b.supplier.return_cutoff_days)
        add("expiry", "warning", f"{_bdt(sum(b.qty * b.unit_cost for b in expiring))} of stock expires within 60 days",
            f"{len(expiring)} batches. {past} of them are past their return window.")

    old = [d for d in db.scalars(select(m.PatientDue).where(m.PatientDue.pharmacy_id == pid))
           if d.since < today - timedelta(days=30)]
    if old:
        add("patient_dues", "info", f"{_bdt(sum(d.amount for d in old))} of patient dues is over 30 days old",
            f"{len(old)} customers owe money from more than a month ago.")

    for cap in db.scalars(select(m.Capture).where(m.Capture.pharmacy_id == pid)):
        if cap.extraction.get("suspicious_text"):
            add("suspicious_document", "critical", "A photo contained instructions",
                f"Capture {cap.id} had text that looked like instructions. It was ignored; please check the document.")
    return [Alert.model_validate(a) for a in alerts]

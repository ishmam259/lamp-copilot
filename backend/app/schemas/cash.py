from typing import Literal

from .common import ISODate, Model, Timestamp


class ForecastItem(Model):
    label: str
    amount: float  # signed: + inflow, - outflow


class ForecastDay(Model):
    date: ISODate
    inflow: float
    outflow: float
    balance: float
    items: list[ForecastItem] = []


class Shortfall(Model):
    date: ISODate
    amount: float
    cause: str


class ForecastOut(Model):
    start_cash: float
    days: list[ForecastDay]
    shortfalls: list[Shortfall]


AlertKind = Literal["shortfall", "expiry", "return_window", "patient_dues", "suspicious_document"]


class Alert(Model):
    id: str
    kind: AlertKind
    severity: Literal["critical", "warning", "info"]
    title: str
    detail: str
    created_at: Timestamp

from typing import Literal

from .common import ISODate, Model


class SupplierShare(Model):
    name: str
    share_pct: float


class SlowMover(Model):
    product: str
    qty: int
    sellable_qty: int
    at_risk_value: float


class AccountsOut(Model):
    period_days: int
    sales: float
    gross_margin_pct: float
    gross_profit: float
    overheads: float
    net_profit: float
    stock_value: float
    stock_days: float
    patient_dues: float
    patient_due_days: float
    active_suppliers: int
    top_suppliers: list[SupplierShare]
    slow_movers: list[SlowMover]
    expiring_value_60d: float


DueStatus = Literal["overdue", "due_soon", "upcoming"]


class DueItem(Model):
    supplier: str
    invoice_no: str
    amount: float
    due_date: ISODate
    days_left: int
    status: DueStatus


class DuesOut(Model):
    items: list[DueItem]
    total_due: float


class WalletTxnOut(Model):
    date: ISODate
    amount: float
    kind: str
    ref: str


class StatementMatch(Model):
    ref: str
    date: ISODate
    amount: float
    payee: str
    status: Literal["matched", "duplicate", "unmatched", "missing_from_statement"]
    invoice_no: str | None = None
    supplier: str | None = None
    note: str


class AccountOut(Model):
    """Sandbox wallet and its reconciliation (win plan CORE-05)."""

    opening_balance: float
    balance: float
    transactions: list[WalletTxnOut]
    matches: list[StatementMatch]
    counts: dict[str, int]
    recommendations: list[str]

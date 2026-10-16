from .common import ISODate, Model


class OrderLine(Model):
    product: str
    qty: int
    unit_cost: float


class OrderOut(Model):
    id: str
    supplier: str
    due_date: ISODate
    total: float
    lines: list[OrderLine]


class TrimLine(Model):
    product: str
    qty: int
    unit_cost: float
    sales_rate_per_day: float
    sellable_days: int
    sellable_qty: int
    suggested_qty: int
    at_risk_value: float


class TrimOut(Model):
    order_id: str
    lines: list[TrimLine]
    original_total: float
    suggested_total: float
    saving: float

from .common import ISODate, Model


class ExpiryBatch(Model):
    product: str
    batch_no: str
    expiry_date: ISODate
    days_left: int
    qty: int
    cost_value: float
    return_eligible: bool
    supplier: str


class ExpiryOut(Model):
    horizon_days: int
    batches: list[ExpiryBatch]
    at_risk_value: float
    return_eligible_value: float

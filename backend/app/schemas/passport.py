from .common import ISODate, Model


class PassportEvidence(Model):
    invoice_no: str
    supplier: str
    due_date: ISODate
    paid_on: ISODate
    on_time: bool
    supplier_confirmed: bool


class PassportOut(Model):
    invoices_total: int
    paid_on_time: int
    confirmed_share: float
    theta_mean: float
    theta_low_5pct: float
    default_probability: float
    score: float
    advance_rate_pct: float
    partner_share_pct: float
    evidence: list[PassportEvidence]

from typing import Literal

from .common import Model, Timestamp
from .passport import PassportOut


class LenderProduct(Model):
    key: str
    label: str
    apr_pct: float | None
    fee_pct: float | None
    min_amount: float
    max_amount: float


class LenderOut(Model):
    id: str
    name: str
    kind: Literal["mobile_wallet", "bank"]
    products: list[LenderProduct]


class ConsentIn(Model):
    lender_id: str
    scopes: list[str] = ["passport", "accounts"]


class ConsentOut(Model):
    id: str
    lender_id: str
    scopes: list[str]
    granted_at: Timestamp


class ConsentPreview(Model):
    """What a lender would see with these scopes (win plan CORE-16)."""

    lender_id: str
    scopes: list[str]
    shares: list[str]
    withholds: list[str]
    passport: PassportOut


class Decision(Model):
    approved: bool
    payout_ref: str | None = None
    reason: str


class ApplicationOut(Model):
    id: str
    pharmacy_id: str
    pharmacy_name: str
    lender_id: str
    product_key: str
    amount: float
    status: Literal["pending", "approved", "declined"]
    passport: PassportOut
    decision: Decision | None = None
    created_at: Timestamp

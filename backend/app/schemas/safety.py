"""Win-plan v3 contract: session, Pause, follow-ups, log verification, shelf-life credit.

Endpoints (all under /api/v1):
- POST /pharmacies/{pid}/session        SessionIn -> SessionOut, sets the HttpOnly cookie
- POST /pharmacies/{pid}/pause          PauseIn -> PauseOut
- GET  /pharmacies/{pid}/pause          PauseOut
- GET  /pharmacies/{pid}/followups      list[FollowUpOut]
- GET  /pharmacies/{pid}/shelf-life-credit  ShelfLifeCreditOut
- GET  /logs/verify                     VerifyOut
- POST /pharmacies/{pid}/actions/{aid}/approve  body ApprovalIn (pin needed when ActionOut.requires_pin)

Notify events travel on the existing log stream as LogEvent rows with component "NOTIFY",
event "notify" and data NotifyData.
"""

from typing import Literal

from .common import ExplainRow, ISODate, Model, Timestamp


class SessionIn(Model):
    pin: str


class SessionOut(Model):
    pharmacy_id: str
    role: Literal["owner"]
    expires_at: Timestamp


class ApprovalIn(Model):
    pin: str | None = None


class PauseIn(Model):
    paused: bool


class PauseOut(Model):
    paused: bool
    changed_at: Timestamp | None = None


class FollowUpOut(Model):
    id: str
    plan_action_id: str            # the extension request this follow-up watches
    fallback_kind: Literal["loan_application"]
    fallback_payload: dict
    amount: float
    deadline: ISODate              # supplier must answer by this date (story time)
    status: Literal["waiting", "fired", "cancelled"]
    fired_action_id: str | None = None
    created_at: Timestamp


class VerifyOut(Model):
    intact: bool
    count: int
    head_hash: str | None
    first_bad_id: str | None = None


class ShelfLifeBatch(Model):
    product: str
    qty_ordered: int
    sellable_qty: int
    unsellable_value: float


class ShelfLifeCreditOut(Model):
    order_id: str
    needed_by: ISODate
    counterfactual_purpose_blind: float  # what a lender that ignores the shelf would finance
    not_financed: float                  # order stock that won't sell before expiry
    financeable: float
    reason: str
    batches: list[ShelfLifeBatch]
    explain: list[ExplainRow] = []  # purpose-blind − not financed = financeable


class DbrCheck(Model):
    label: str
    amount: float
    months: int
    monthly_repayment: float
    existing_monthly_repayment: float = 0  # loans a lender has already approved
    monthly_net_cash_flow: float
    dbr_pct: float | None
    cap_pct: float
    ok: bool


class PolicyOut(Model):
    """The rules LaMP enforces (win plan CORE-07/08): Pause, PIN, the borrowing ceiling."""

    paused: bool
    pin_required_for: list[str]
    dbr_cap_pct: float
    monthly_net_cash_flow: float
    source: dict[str, str | int]
    examples: list[DbrCheck]


class NotifyData(Model):
    audience: Literal["owner", "admin"]
    title: str
    body: str
    link: str | None = None

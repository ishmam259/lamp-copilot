from .actions import ActionKind
from .common import Certainty, ISODate, Model


class FundingNeed(Model):
    amount: float
    needed_by: ISODate


class FundingRequest(Model):
    """POST body for /funding-plan. Every field is optional: an empty body (or none)
    means the default need, and a missing field is filled from that default."""

    amount: float | None = None
    needed_by: ISODate | None = None


class FundingOption(Model):
    key: str
    label: str
    provider: str
    amount: float
    cost_bdt: float | None
    apr_pct: float | None
    eligible: bool
    reason: str
    speed: str
    certainty: Certainty


class PlanStep(Model):
    action_kind: ActionKind
    label: str
    amount: float
    when: ISODate
    fallback_for: str | None = None


class FundingPlan(Model):
    steps: list[PlanStep]
    total_cost_bdt: float


class FundingPlanOut(Model):
    need: FundingNeed
    options: list[FundingOption]
    plan: FundingPlan
    naive_cost_bdt: float

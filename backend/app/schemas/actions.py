from typing import Any, Literal

from .common import Model, Timestamp

ActionKind = Literal["return_claim", "extension_request", "loan_application", "set_aside", "trim_order"]
ActionStatus = Literal["proposed", "approved", "rejected", "executed", "failed"]
ProposedBy = Literal["owner", "agent"]


class ActionProposal(Model):
    kind: ActionKind
    payload: dict[str, Any] = {}
    proposed_by: ProposedBy | None = None  # may also come as a query parameter; default "owner"


class SupplierReply(Model):
    action_id: str
    accepted: bool


class ActionOut(Model):
    id: str
    kind: ActionKind
    status: ActionStatus
    payload: dict[str, Any]
    proposed_by: ProposedBy
    created_at: Timestamp
    decided_at: Timestamp | None = None
    result: dict[str, Any] | None = None

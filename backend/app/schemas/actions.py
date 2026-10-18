from typing import Any, Literal

from .common import Model, Timestamp

ActionKind = Literal["return_claim", "extension_request", "loan_application", "set_aside", "trim_order"]
ActionStatus = Literal["proposed", "approved", "rejected", "executed", "failed"]
ProposedBy = Literal["owner", "agent", "lamp-scheduler"]


class ActionProposal(Model):
    kind: ActionKind
    payload: dict[str, Any] = {}
    proposed_by: ProposedBy | None = None  # ignored over HTTP: the caller is taken from the session


class SupplierReply(Model):
    """Demo simulator body: `outcome`, or the older `accepted` flag."""

    action_id: str
    accepted: bool | None = None
    outcome: Literal["accepted", "declined", "no_reply"] | None = None

    def resolved(self) -> str:
        if self.outcome:
            return self.outcome
        return "accepted" if self.accepted else "declined"


class ActionOut(Model):
    id: str
    kind: ActionKind
    status: ActionStatus
    payload: dict[str, Any]
    proposed_by: ProposedBy
    created_at: Timestamp
    decided_at: Timestamp | None = None
    result: dict[str, Any] | None = None
    requires_pin: bool = False  # approve must re-enter the owner PIN (loan applications)

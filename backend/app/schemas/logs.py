from typing import Any, Literal

from .common import Model, Timestamp

Tier = Literal["T0", "T1", "T2", "T3"]


class LogEvent(Model):
    id: str
    ts: Timestamp
    tier: Tier
    component: str
    event: str
    data: dict[str, Any] = {}
    hash: str | None = None  # sha256(prev_hash + canonical event): the audit log is a hash chain

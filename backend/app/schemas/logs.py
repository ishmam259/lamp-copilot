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

from datetime import date, datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict


def _utc(v: datetime) -> datetime:
    # Stored timestamps are UTC; the databases hand them back without a zone.
    return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)


ISODate = date
Timestamp = Annotated[datetime, AfterValidator(_utc)]  # always serialized with a UTC offset
Certainty = Literal["certain", "uncertain"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

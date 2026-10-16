from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ISODate = date
Timestamp = datetime
Certainty = Literal["certain", "uncertain"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

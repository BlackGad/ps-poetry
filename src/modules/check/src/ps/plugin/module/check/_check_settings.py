from typing import Optional
from pydantic import BaseModel, Field


class CheckSettings(BaseModel):
    checks: Optional[list[str]] = Field(default=None, alias="checks")

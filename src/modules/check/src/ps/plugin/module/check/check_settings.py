from typing import Optional
from pydantic import BaseModel, Field


class CheckSettings(BaseModel):
    checks_include: Optional[list[str]] = Field(default=None, alias="checks-include")
    checks_exclude: Optional[list[str]] = Field(default=None, alias="checks-exclude")

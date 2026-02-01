from typing import Optional
from pydantic import BaseModel, Field


class DeliverySettings(BaseModel):
    version_pattern: Optional[str] = Field(default=None, alias="version-pattern")

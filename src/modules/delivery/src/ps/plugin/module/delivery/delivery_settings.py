from typing import Optional
from pydantic import BaseModel, Field


class DeliverySettings(BaseModel):
    version_patterns: Optional[list[str]] = Field(default_factory=list, alias="version-patterns")

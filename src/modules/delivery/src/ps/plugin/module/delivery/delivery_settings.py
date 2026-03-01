from typing import Optional
from pydantic import BaseModel, Field
from ps.version import VersionConstraint


class DeliverySettings(BaseModel):
    version_patterns: Optional[list[str]] = Field(default_factory=list, alias="version-patterns")
    version_pinning: Optional[VersionConstraint] = Field(default=VersionConstraint.COMPATIBLE, alias="version-pinning")

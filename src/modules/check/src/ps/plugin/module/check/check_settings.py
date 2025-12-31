from typing import Optional
from pydantic import BaseModel


class CheckSettings(BaseModel):
    include_checks: Optional[list[str]] = None
    exclude_checks: Optional[list[str]] = None

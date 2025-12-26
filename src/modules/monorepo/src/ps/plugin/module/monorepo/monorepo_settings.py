from enum import Enum
from pydantic import BaseModel


class MonorepoProjectMode(Enum):
    DISABLED = "disabled"
    HOST = "host"
    CHILD = "child"


class MonorepoSettings(BaseModel):
    monorepo: MonorepoProjectMode = MonorepoProjectMode.DISABLED

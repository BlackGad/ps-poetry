from typing import ClassVar
from pydantic import BaseModel, ConfigDict


class PluginSettings(BaseModel):
    NAME: ClassVar[str] = "ps-plugin-host"

    enabled: bool = False

    model_config = ConfigDict(
        extra="allow",
    )

from pathlib import Path
from typing import ClassVar, Optional
from pydantic import BaseModel, ConfigDict, Field


class PluginSettings(BaseModel):
    NAME: ClassVar[str] = "ps-plugin"

    enabled: Optional[bool] = Field(default=None, exclude=True)
    host_project: Optional[Path] = Field(default=None, alias="host-project")
    modules: Optional[list[str]] = Field(default=None, alias="modules")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

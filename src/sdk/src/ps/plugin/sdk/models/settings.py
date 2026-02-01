from enum import Enum
from pathlib import Path
from typing import ClassVar, Optional
from pydantic import BaseModel, ConfigDict, Field


class PackageManagerMode(Enum):
    CENTRAL = "central"
    MESH = "mesh"


class PluginSettings(BaseModel):
    NAME: ClassVar[str] = "ps-plugin"

    enabled: Optional[bool] = Field(default=None, exclude=True)
    host_project: Optional[Path] = Field(default=None, alias="host-project")
    modules_include: Optional[list[str]] = Field(default=None, alias="modules-include")
    modules_exclude: Optional[list[str]] = Field(default=None, alias="modules-exclude")
    package_manager: Optional[PackageManagerMode] = Field(default=PackageManagerMode.CENTRAL, alias="package-manager")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

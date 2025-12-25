from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from tomlkit import TOMLDocument


class ProjectDependency(BaseModel):
    defined_name: Optional[str] = None
    defined_version: Optional[str] = None

    # Resolution
    resolved_name: Optional[str] = None
    resolved_version: Optional[str] = None

    # Classification
    group: Optional[str] = None
    optional: Optional[bool] = None
    python: Optional[str] = None
    markers: Optional[str] = None
    extras: Optional[list[str]] = None
    source: Optional[str] = None

    # Location-based
    path: Optional[Path] = None
    develop: Optional[bool] = None
    url: Optional[str] = None

    # VCS
    git: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    rev: Optional[str] = None


class Project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    defined_name: Optional[str] = None
    defined_version: Optional[str] = None
    path: Path
    document: TOMLDocument = Field(exclude=True)
    dependencies: list[ProjectDependency]

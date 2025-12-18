from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from tomlkit import TOMLDocument


class ProjectDependency(BaseModel):
    defined_name: str
    defined_version: str
    resolved_name: Optional[str] = None
    resolved_version: Optional[str] = None
    path: Optional[Path] = None


class Project(BaseModel):
    defined_name: str
    defined_version: str
    path: Path
    document: TOMLDocument


class Solution(BaseModel):
    root_project_name: str
    affected_project_names: str
    projects: dict[str, Project]

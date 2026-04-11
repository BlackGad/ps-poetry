from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VersionPatternResult:
    pattern: str
    condition: str = ""
    condition_matched: Optional[bool] = None
    resolved_raw: str = ""
    matched: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class DependencyResolution:
    name: str
    constraint: str
    is_project: bool = False
    path: str = ""
    source: str = ""


@dataclass
class ProjectResolution:
    name: str
    path: str
    version: str
    deliver: str
    pinning: str = ""
    matched_pattern: str = ""
    pattern_results: list[VersionPatternResult] = field(default_factory=list)
    dependencies: list[DependencyResolution] = field(default_factory=list)


@dataclass
class ProjectSummary:
    name: str
    version: str
    deliver: str


@dataclass
class DependencyNode:
    name: str
    version: str
    children: list["DependencyNode"] = field(default_factory=list)


@dataclass
class PublishWave:
    index: int
    projects: list[ProjectSummary] = field(default_factory=list)

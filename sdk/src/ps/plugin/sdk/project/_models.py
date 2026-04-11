import os
from enum import StrEnum
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from tomlkit import TOMLDocument, inline_table, table as toml_table
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from ps.version import Version, VersionConstraint

from ..settings._settings import PluginSettings
from ..toml._toml_value import TomlValue


def normalize_dist_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(".", "_")


def dist_name_variants(name: str) -> set[str]:
    lower = name.lower()
    return {
        lower,
        lower.replace("-", "_").replace(".", "_"),
        lower.replace("_", "-"),
    }


class SourcePriority(StrEnum):
    DEFAULT = "default"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUPPLEMENTAL = "supplemental"
    EXPLICIT = "explicit"


class ProjectFeedSource(BaseModel):
    name: str
    url: Optional[str] = None
    priority: Optional[SourcePriority] = None


class ProjectDependency(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    location: TomlValue = Field(exclude=True)
    name: Optional[str] = None

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

    @property
    def version(self) -> Optional[str]:
        if not self.location.exists:
            return None

        current_value = self.location.value
        if isinstance(current_value, str):
            # Either PEP 508 string or Poetry simple string
            try:
                req = Requirement(current_value)
                return str(req.specifier) if req.specifier else "*"
            except (ValueError, TypeError):
                # Poetry simple string format
                return current_value
        elif isinstance(current_value, dict):
            # Poetry dict format
            version = current_value.get("version")
            return str(version) if version is not None else None

        return None

    @property
    def version_constraint(self) -> Optional[SpecifierSet]:
        version_str = self.version
        if not version_str:
            return None
        try:
            # Handle Poetry wildcard (any version)
            if version_str == "*":
                return SpecifierSet("")
            # Convert Poetry caret syntax to PEP 440
            if version_str.startswith("^"):
                version_str = self._convert_caret_to_pep440(version_str[1:])
            return SpecifierSet(version_str)
        except (ValueError, TypeError):
            return None

    def _convert_caret_to_pep440(self, version_str: str) -> str:
        try:
            version = Version.parse(version_str)
            assert version is not None, "Invalid version for caret syntax"
            return version.get_constraint(VersionConstraint.COMPATIBLE)
        except Exception:
            # Fallback to original if parsing fails
            return f"^{version_str}"

    def update_version(self, version_constraint: str | SpecifierSet) -> None:
        if not self.location.exists:
            return

        # Convert SpecifierSet to string
        constraint_str = str(version_constraint) if isinstance(version_constraint, SpecifierSet) else version_constraint

        current_value = self.location.value

        if isinstance(current_value, str):
            # PEP 621/508 format: reconstruct the requirement string
            self._update_pep508_version(constraint_str)
        elif isinstance(current_value, dict):
            # Poetry dict format
            # Switch path/VCS/url dependencies to plain constraint
            # to avoid invalid mixed-table definitions.
            is_source_dependency = any(key in current_value for key in ("path", "git", "url"))
            if is_source_dependency:
                self.location.set(constraint_str)
            else:
                current_value["version"] = constraint_str
                self.location.set(current_value)
        else:
            # Poetry simple string format: replace entire value
            self.location.set(constraint_str)

    def _update_pep508_version(self, version_constraint: str) -> None:
        try:
            current = self.location.value
            if not isinstance(current, str):
                return

            req = Requirement(current)

            # Reconstruct with new version constraint
            parts = [req.name]
            if self.extras:
                parts.append(f"[{','.join(self.extras)}]")
            parts.append(version_constraint)
            if req.marker:
                parts.append(f"; {req.marker}")

            self.location.set("".join(parts))
        except (ValueError, TypeError):
            # Fallback: just set the version string
            self.location.set(version_constraint)

    @property
    def resolved_project_path(self) -> Optional[Path]:
        if self.path is None:
            return None
        if self.path.suffix == ".toml":
            return self.path.resolve()
        return (self.path / "pyproject.toml").resolve()


class Project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: TomlValue
    version: TomlValue
    path: Path
    document: TOMLDocument = Field(exclude=True)
    dependencies: list[ProjectDependency]
    sources: list[ProjectFeedSource]
    source_dirs: list[Path]
    plugin_settings: PluginSettings

    def save(self) -> None:
        with open(self.path, "w") as f:
            f.write(self.document.as_string())

    def add_dependency(
        self,
        name: str,
        constraint: Optional[str] = None,
        group: Optional[str] = None,
    ) -> "ProjectDependency":
        entry: Any = constraint if constraint is not None else "*"
        return self._write_dependency(name, entry, resolved_path=None, develop=None, group=group)

    def add_development_dependency(
        self,
        name: str,
        path: Path,
        group: Optional[str] = None,
    ) -> "ProjectDependency":
        project_dir = self.path.parent
        entry: Any = inline_table()
        rel = Path(os.path.relpath(path, project_dir))
        entry.append("path", str(rel).replace("\\", "/"))
        entry.append("develop", True)
        return self._write_dependency(name, entry, resolved_path=path.resolve(), develop=True, group=group)

    def _write_dependency(
        self,
        name: str,
        entry: Any,
        resolved_path: Optional[Path],
        develop: Optional[bool],
        group: Optional[str],
    ) -> "ProjectDependency":
        if group is None:
            dep_section = "tool.poetry.dependencies"
            deps_table = self._get_or_create_table("tool", "poetry", "dependencies")
        else:
            dep_section = f"tool.poetry.group.{group}.dependencies"
            group_table = self._get_or_create_table("tool", "poetry", "group", group)
            if "dependencies" not in group_table:
                group_table["dependencies"] = toml_table()
            deps_table = group_table["dependencies"]

        deps_table[name] = entry
        location = TomlValue.locate(self.document, [f"{dep_section}.{name}"])

        dep = ProjectDependency(
            location=location,
            name=name,
            group=group,
            path=resolved_path,
            develop=develop,
        )
        self.dependencies.append(dep)
        return dep

    def _get_or_create_table(self, *keys: str) -> Any:
        current: Any = self.document
        for key in keys:
            if key not in current:
                current[key] = toml_table()
            current = current[key]
        return current

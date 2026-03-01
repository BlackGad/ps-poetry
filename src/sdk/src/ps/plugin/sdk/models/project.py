from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from tomlkit import TOMLDocument
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from .settings import PluginSettings
from .toml_value import TomlValue


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
                return str(req.specifier) if req.specifier else None
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
            return SpecifierSet(version_str)
        except (ValueError, TypeError):
            return None

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
            # Poetry dict format: update version key
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


class Project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: TomlValue
    version: TomlValue
    path: Path
    document: TOMLDocument = Field(exclude=True)
    dependencies: list[ProjectDependency]
    plugin_settings: PluginSettings

    def save(self) -> None:
        with open(self.path, "w") as f:
            f.write(self.document.as_string())

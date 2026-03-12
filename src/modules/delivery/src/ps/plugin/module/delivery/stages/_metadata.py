import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from cleo.io.io import IO
from packaging.specifiers import SpecifierSet

from ps.version import Version, VersionConstraint
from ps.token_expressions import ExpressionFactory
from ps.plugin.sdk.project import (
    Project,
    ProjectDependency,
)

from .._delivery_settings import DeliverySettings

_default_version_patterns: list[str] = [
    "[{in}] {in}",
    "[{env:BUILD_VERSION}] {env:BUILD_VERSION}",
    "{spec}"
]
_default_version: Version = Version()


def _format_date(dt: datetime, cs_format: str) -> str:
    py_format = (
        cs_format
        .replace("yyyy", "\x00YYYY\x00")
        .replace("yy", "\x00YY\x00")
        .replace("MM", "\x00MONTH\x00")
        .replace("dd", "\x00DAY\x00")
        .replace("HH", "\x00HOUR24\x00")
        .replace("mm", "\x00MINUTE\x00")
        .replace("ss", "\x00SEC\x00")
        .replace("\x00YYYY\x00", "%Y")
        .replace("\x00YY\x00", "%y")
        .replace("\x00MONTH\x00", "%m")
        .replace("\x00DAY\x00", "%d")
        .replace("\x00HOUR24\x00", "%H")
        .replace("\x00MINUTE\x00", "%M")
        .replace("\x00SEC\x00", "%S")
    )
    return dt.strftime(py_format)


@dataclass
class ResolvedDependencyVersion:
    dependency: ProjectDependency
    version_constraint: SpecifierSet


@dataclass
class ResolvedProjectMetadata:
    pinning: VersionConstraint = VersionConstraint.COMPATIBLE
    version: Version = field(default_factory=Version)
    dependencies: list[ResolvedDependencyVersion] = field(default_factory=list)
    project_dependencies: list[Path] = field(default_factory=list)
    deliver: bool = True


@dataclass
class ResolvedEnvironmentMetadata:
    projects: dict[Path, ResolvedProjectMetadata] = field(default_factory=dict)


def _split_version_pattern(pattern: str) -> tuple[Optional[str], str]:
    if pattern.startswith("["):
        end_bracket = pattern.find("]")
        if end_bracket != -1:
            condition = pattern[1:end_bracket]
            version = pattern[end_bracket + 1:].lstrip()
            return condition, version
    return None, pattern


def _validate_and_match_condition(io: IO, factory: ExpressionFactory, condition_pattern: str) -> bool:
    condition_validation_result = factory.validate_match(condition_pattern)
    if not condition_validation_result.success:
        if io.is_debug():
            io.write_line(f"  <fg=dark_gray>- Version: Condition '<fg=cyan>{condition_pattern}</> did not match (validation failed).</>")
            for error in condition_validation_result.errors:
                io.write_line(f"    <fg=dark_gray>- <fg=red>{error}</></>")
        return False
    if not factory.match(condition_pattern):
        if io.is_debug():
            io.write_line(f"  <fg=dark_gray>- Version: Condition '<fg=cyan>{condition_pattern}</> evaluated to false.</>")
        return False
    return True


def _resolve_version_from_pattern(
    io: IO,
    factory: ExpressionFactory,
    version_pattern: str,
    default_version: Version,
) -> Optional[tuple[Version, str]]:
    version_validation_result = factory.validate_materialize(version_pattern)
    if not version_validation_result.success:
        if io.is_debug():
            io.write_line(f"  <fg=dark_gray>- Version pattern '<fg=cyan>{version_pattern}</> is invalid.</>")
            for error in version_validation_result.errors:
                io.write_line(f"    <fg=dark_gray>- <fg=red>{error}</></>")
        return None

    raw_version = factory.materialize(version_pattern)
    parsed_version = Version.parse(raw_version)
    if parsed_version is None and io.is_debug():
        io.write_line(f"  <fg=dark_gray>- Version pattern '<fg=cyan>{version_pattern}</> resolved to '<fg=yellow>{raw_version}</> but is not a valid version.</>")

    return parsed_version or default_version, version_pattern


def _resolve_project_version(
    io: IO,
    factory: ExpressionFactory,
    version_patterns: list[str],
    pinning_rule: VersionConstraint,
) -> Optional[Version]:
    for pattern in version_patterns:
        condition_pattern, version_pattern = _split_version_pattern(pattern)
        if condition_pattern is not None and not _validate_and_match_condition(io, factory, condition_pattern):
            continue

        resolved_tuple = _resolve_version_from_pattern(io, factory, version_pattern, _default_version)
        if resolved_tuple:
            version, matched_pattern = resolved_tuple
            if io.is_verbose():
                io.write_line(f"  - Version: <fg=green>{version}</> (Pattern: '<fg=cyan>{matched_pattern}</>', Pinning rule: <fg=cyan>{pinning_rule.value}</>)")
            else:
                io.write_line(f"  - Version: <fg=green>{version}</>")
            return version

    return None


def _resolve_project_dependencies(
    io: IO,
    project: Project,
    host_dependencies: dict[str, ProjectDependency],
) -> tuple[list[ResolvedDependencyVersion], list[Path]]:
    resolved: list[ResolvedDependencyVersion] = []
    project_dependency_paths: list[Path] = []

    project_deps = [dep for dep in project.dependencies if dep.path is not None and dep.develop]
    third_party_deps = [dep for dep in project.dependencies if dep.path is None or not dep.develop]

    for dep in project_deps:
        base_line = f"  - Project dependency '<fg=cyan>{dep.name}</>'"
        if io.is_verbose():
            io.write_line(f"{base_line} [<fg=dark_gray>{dep.path}</>]")
        else:
            io.write_line(base_line)

        assert dep.path is not None  # Filtered above
        path = (dep.path if dep.path.suffix == ".toml" else dep.path / "pyproject.toml").resolve()
        project_dependency_paths.append(path)

        constraint = dep.version_constraint
        if constraint is None:
            continue

        resolved.append(ResolvedDependencyVersion(dependency=dep, version_constraint=constraint))

    for dep in third_party_deps:
        constraint = dep.version_constraint
        if constraint is None:
            if io.is_debug():
                io.write_line(f"  <fg=dark_gray>- Dependency '<fg=cyan>{dep.name}</> skipped (no version constraint).</>")
            continue

        detail: Optional[str] = None
        if str(constraint) == "":
            dep_name = dep.name
            host_dep = host_dependencies.get(dep_name) if dep_name else None
            host_constraint = host_dep.version_constraint if host_dep else None
            if host_constraint:
                constraint = host_constraint
                detail = f"Resolved from <fg=cyan>host</>: <fg=green>{host_constraint}</>"
            else:
                detail = f"from <fg=cyan>{'host-no-constraint' if host_dep else 'not-found'}</>"
        elif io.is_debug():
            detail = "<fg=dark_gray>direct</>"

        base_line = f"  - Dependency '<fg=cyan>{dep.name}</>': <fg=green>{constraint}</>"
        if detail and io.is_verbose():
            io.write_line(f"{base_line} ({detail})")
        elif not io.is_debug() or detail:
            io.write_line(base_line)

        resolved.append(ResolvedDependencyVersion(dependency=dep, version_constraint=constraint))

    return resolved, project_dependency_paths


def resolve_environment_metadata(
    io: IO,
    input_version: Optional[Version],
    host_project: Project,
    projects: Iterable[Project],
) -> ResolvedEnvironmentMetadata:
    resolved_projects: dict[Path, ResolvedProjectMetadata] = {}
    host_project_delivery_settings = DeliverySettings.model_validate(host_project.plugin_settings.model_dump())
    host_project_version = Version.parse(host_project.version.value) or _default_version
    host_dependencies: dict[str, ProjectDependency] = {
        dep.name: dep
        for dep in host_project.dependencies
        if dep.name and dep.version_constraint
    }

    projects = list(projects)
    now = datetime.now()

    for project in projects:
        project_display_name = project.name.value or project.path.name
        project_delivery_settings = DeliverySettings.model_validate(project.plugin_settings.model_dump())
        version_patterns = project_delivery_settings.version_patterns or host_project_delivery_settings.version_patterns or _default_version_patterns
        pinning_rule = project_delivery_settings.version_pinning or host_project_delivery_settings.version_pinning or VersionConstraint.COMPATIBLE

        io.write_line(f"<fg=magenta>Resolving project:</> <fg=blue>{project_display_name}</> [<fg=dark_gray>{project.path}</>]")

        if io.is_debug():
            for i, pattern in enumerate(version_patterns, 1):
                io.write_line(f"  <fg=dark_gray>- Version pattern [{i}]: '<fg=cyan>{pattern}</>'</>")

        project_spec_version = Version.parse(project.version.value)
        if project_spec_version is None or project_spec_version == _default_version:
            project_spec_version = host_project_version

        factory = ExpressionFactory(
            token_resolvers=[
                ("in", input_version),
                ("env", lambda arg: os.getenv(arg) if arg else None),
                ("env-ver", lambda arg: Version.parse(os.getenv(arg)) if arg else None),
                ("spec", project_spec_version),
                ("date", lambda arg: _format_date(now, arg) if arg else str(now.date())),
            ],
            default_callback=lambda _key, _args: ""
        )

        metadata = ResolvedProjectMetadata()
        metadata.pinning = pinning_rule
        metadata.deliver = project_delivery_settings.deliver
        version = _resolve_project_version(io, factory, version_patterns, pinning_rule)
        if version is not None:
            metadata.version = version
        metadata.dependencies, metadata.project_dependencies = _resolve_project_dependencies(io, project, host_dependencies)
        resolved_projects[project.path] = metadata

    return ResolvedEnvironmentMetadata(projects=resolved_projects)

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from packaging.specifiers import SpecifierSet

from ps.plugin.sdk.project._environment import Environment
from ps.version import Version, VersionConstraint
from ps.token_expressions import ExpressionFactory, TokenResolverEntry
from ps.plugin.sdk.project import (
    Project,
    ProjectDependency,
)

from ps.plugin.sdk.toml import TomlValue

from .._delivery_settings import DeliverySettings
from ..output import DependencyResolution, ProjectResolution, VersionPatternResult

_default_version_patterns: list[str] = [
    "[{in}] {in}",
    "[{env:BUILD_VERSION}] {env:BUILD_VERSION}",
    "{spec}"
]
_default_version: Version = Version()


class DeliverableType(Enum):
    ENABLED = "Enabled"
    DISABLED_BY_PACKAGE_MODE = "DisabledByPackageMode"
    DISABLED_BY_DELIVERABLE_OPTION = "DisabledByDeliverableOption"


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
    deliver: DeliverableType = DeliverableType.ENABLED


@dataclass
class ResolvedEnvironmentMetadata:
    projects: dict[Path, ResolvedProjectMetadata] = field(default_factory=dict)
    resolutions: list[ProjectResolution] = field(default_factory=list)


def _split_version_pattern(pattern: str) -> tuple[Optional[str], str]:
    if pattern.startswith("["):
        end_bracket = pattern.find("]")
        if end_bracket != -1:
            condition = pattern[1:end_bracket]
            version = pattern[end_bracket + 1:].lstrip()
            return condition, version
    return None, pattern


def _validate_and_match_condition(factory: ExpressionFactory, condition_pattern: str) -> tuple[bool, list[str]]:
    condition_validation_result = factory.validate_match(condition_pattern)
    if not condition_validation_result.success:
        return False, [str(e) for e in condition_validation_result.errors]
    if not factory.match(condition_pattern):
        return False, []
    return True, []


def _resolve_version_from_pattern(
    factory: ExpressionFactory,
    version_pattern: str,
    default_version: Version,
) -> tuple[Optional[tuple[Version, str]], str, list[str]]:
    version_validation_result = factory.validate_materialize(version_pattern)
    if not version_validation_result.success:
        return None, "", [str(e) for e in version_validation_result.errors]

    raw_version = factory.materialize(version_pattern)
    parsed_version = Version.parse(raw_version)
    errors: list[str] = []
    if parsed_version is None:
        errors.append(f"Resolved to '{raw_version}' but is not a valid version.")

    return (parsed_version or default_version, version_pattern), raw_version, errors


def _resolve_project_version(
    factory: ExpressionFactory,
    version_patterns: list[str],
) -> tuple[Optional[Version], str, list[VersionPatternResult]]:
    pattern_results: list[VersionPatternResult] = []
    matched_pattern = ""
    for pattern in version_patterns:
        condition_pattern, version_pattern = _split_version_pattern(pattern)

        result = VersionPatternResult(pattern=pattern)
        if condition_pattern is not None:
            matched, errors = _validate_and_match_condition(factory, condition_pattern)
            result.condition = condition_pattern
            result.condition_matched = matched
            result.errors = errors
            if not matched:
                pattern_results.append(result)
                continue

        resolved, raw, errors = _resolve_version_from_pattern(factory, version_pattern, _default_version)
        result.resolved_raw = raw
        result.errors.extend(errors)
        if resolved:
            version, matched_pattern = resolved
            result.matched = True
            pattern_results.append(result)
            return version, matched_pattern, pattern_results

        pattern_results.append(result)

    return None, matched_pattern, pattern_results


def _resolve_project_dependencies(
    project: Project,
    host_dependencies: dict[str, ProjectDependency],
) -> tuple[list[ResolvedDependencyVersion], list[Path], list[DependencyResolution]]:
    resolved: list[ResolvedDependencyVersion] = []
    project_dependency_paths: list[Path] = []
    dep_resolutions: list[DependencyResolution] = []

    project_deps = [dep for dep in project.dependencies if dep.path is not None and dep.develop]
    third_party_deps = [dep for dep in project.dependencies if dep.path is None or not dep.develop]

    for dep in project_deps:
        assert dep.path is not None
        path = (dep.path if dep.path.suffix == ".toml" else dep.path / "pyproject.toml").resolve()
        project_dependency_paths.append(path)

        dep_resolutions.append(DependencyResolution(
            name=dep.name or "",
            constraint=str(dep.version_constraint or ""),
            is_project=True,
            path=str(dep.path),
        ))

        constraint = dep.version_constraint
        if constraint is None:
            continue
        resolved.append(ResolvedDependencyVersion(dependency=dep, version_constraint=constraint))

    for dep in third_party_deps:
        constraint = dep.version_constraint
        if constraint is None:
            dep_resolutions.append(DependencyResolution(
                name=dep.name or "",
                constraint="",
                source="skipped",
            ))
            continue

        source = "direct"
        if str(constraint) == "":
            dep_name = dep.name
            host_dep = host_dependencies.get(dep_name) if dep_name else None
            host_constraint = host_dep.version_constraint if host_dep else None
            if host_constraint:
                constraint = host_constraint
                source = "host"
            else:
                source = "host-no-constraint" if host_dep else "not-found"

        dep_resolutions.append(DependencyResolution(
            name=dep.name or "",
            constraint=str(constraint),
            source=source,
        ))
        resolved.append(ResolvedDependencyVersion(dependency=dep, version_constraint=constraint))

    return resolved, project_dependency_paths, dep_resolutions


def resolve_environment_metadata(environment: Environment, resolvers: list[TokenResolverEntry]) -> ResolvedEnvironmentMetadata:
    host_project = environment.host_project

    host_project_delivery_settings = DeliverySettings.model_validate(host_project.plugin_settings.model_dump())
    host_project_version = Version.parse(host_project.version.value) or _default_version
    host_dependencies: dict[str, ProjectDependency] = {
        dep.name: dep
        for dep in host_project.dependencies
        if dep.name and dep.version_constraint
    }

    resolved_projects: dict[Path, ResolvedProjectMetadata] = {}
    resolutions: list[ProjectResolution] = []
    for project in environment.projects:
        project_display_name = project.name.value or project.path.name
        project_delivery_settings = DeliverySettings.model_validate(project.plugin_settings.model_dump())
        version_patterns = project_delivery_settings.version_patterns or host_project_delivery_settings.version_patterns or _default_version_patterns
        pinning_rule = project_delivery_settings.version_pinning or host_project_delivery_settings.version_pinning or VersionConstraint.COMPATIBLE

        package_mode = TomlValue.locate(project.document, ["tool.poetry.package-mode"]).value
        if package_mode is False:
            deliver = DeliverableType.DISABLED_BY_PACKAGE_MODE
        elif project_delivery_settings.deliver is False:
            deliver = DeliverableType.DISABLED_BY_DELIVERABLE_OPTION
        else:
            deliver = DeliverableType.ENABLED

        project_spec_version = Version.parse(project.version.value)
        if project_spec_version is None or project_spec_version == _default_version:
            project_spec_version = host_project_version

        factory = ExpressionFactory(
            token_resolvers=[*resolvers, ("spec", project_spec_version)],
            default_callback=lambda _key, _args: "",
        )

        metadata = ResolvedProjectMetadata()
        metadata.pinning = pinning_rule
        metadata.deliver = deliver
        version, matched_pattern, pattern_results = _resolve_project_version(factory, version_patterns)
        if version is not None:
            metadata.version = version
        metadata.dependencies, metadata.project_dependencies, dep_resolutions = _resolve_project_dependencies(project, host_dependencies)
        resolved_projects[project.path] = metadata

        resolutions.append(ProjectResolution(
            name=project_display_name,
            path=str(project.path),
            version=str(metadata.version),
            deliver=deliver.value,
            pinning=pinning_rule.value,
            matched_pattern=matched_pattern,
            pattern_results=pattern_results,
            dependencies=dep_resolutions,
        ))

    return ResolvedEnvironmentMetadata(projects=resolved_projects, resolutions=resolutions)

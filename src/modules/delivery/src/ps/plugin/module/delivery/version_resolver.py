import os
from dataclasses import dataclass
from typing import Iterable, Optional

from cleo.io.io import IO
from packaging.specifiers import SpecifierSet

from ps.version import Version, VersionConstraint
from ps.token_expressions import ExpressionFactory
from ps.plugin.sdk.models import Project, ProjectDependency

from .delivery_settings import DeliverySettings

_default_version_patterns: list[str] = [
    "[{in}] {in}",
    "[{env:BUILD_VERSION}] {env:BUILD_VERSION}",
    "{spec}"
]
_default_version: Version = Version()


@dataclass
class ResolvedProjectVersion:
    pinning: VersionConstraint
    version: Version


@dataclass
class ResolvedDependencyVersion:
    dependency: ProjectDependency
    version_constraint: SpecifierSet


def _split_version_pattern(pattern: str) -> tuple[Optional[str], str]:
    if pattern.startswith("["):
        end_bracket = pattern.find("]")
        if end_bracket != -1:
            condition = pattern[1:end_bracket]
            version = pattern[end_bracket + 1:].lstrip()
            return condition, version
    return None, pattern


def _validate_and_match_condition(
    io: IO,
    factory: ExpressionFactory,
    condition_pattern: str,
) -> bool:
    condition_validation_result = factory.validate_match(condition_pattern)
    if not condition_validation_result.success:
        if io.is_debug():
            io.write_line(f"    - Condition '<fg=cyan>{condition_pattern}</>' did not match (validation failed).")
            for error in condition_validation_result.errors:
                io.write_line(f"      - {error}")
        return False
    if not factory.match(condition_pattern):
        if io.is_debug():
            io.write_line(f"    - Condition '<fg=cyan>{condition_pattern}</>' evaluated to false.")
        return False
    return True


def _resolve_version_from_pattern(
    io: IO,
    factory: ExpressionFactory,
    version_pattern: str,
    default_version: Version,
    pinning_rule: VersionConstraint,
) -> Optional[tuple[ResolvedProjectVersion, str]]:
    version_validation_result = factory.validate_materialize(version_pattern)
    if not version_validation_result.success:
        if io.is_debug():
            io.write_line(f"    - Version pattern '<fg=cyan>{version_pattern}</>' is invalid.")
            for error in version_validation_result.errors:
                io.write_line(f"      - {error}")
        return None

    raw_version = factory.materialize(version_pattern)
    parsed_version = Version.parse(raw_version)
    if parsed_version is None:
        if io.is_debug():
            io.write_line(
                f"    - Version pattern '<fg=cyan>{version_pattern}</>' resolved to '<fg=yellow>{raw_version}</>' but is not a valid version."
            )
        return ResolvedProjectVersion(pinning=pinning_rule, version=default_version), version_pattern

    return ResolvedProjectVersion(pinning=pinning_rule, version=parsed_version), version_pattern


def resolve_project_versions(io: IO, input_version: Optional[Version], host_project: Project, filtered_projects: Iterable[Project]) -> dict[str, ResolvedProjectVersion]:
    result: dict[str, ResolvedProjectVersion] = {}
    host_project_delivery_settings = DeliverySettings.model_validate(host_project.plugin_settings.model_dump())
    host_project_version = Version.parse(host_project.version.value) or _default_version

    for project in filtered_projects:
        project_display_name = project.name.value or project.path.name
        project_delivery_settings = DeliverySettings.model_validate(project.plugin_settings.model_dump())
        project_version_patterns = project_delivery_settings.version_patterns or host_project_delivery_settings.version_patterns or _default_version_patterns
        pinning_rule = project_delivery_settings.version_pinning or host_project_delivery_settings.version_pinning or VersionConstraint.COMPATIBLE

        io.write_line(f"Resolving project: <fg=cyan>{project_display_name}</> [<fg=dark_gray>{project.path}</>]")

        # Use host_project_version if project.version.value is None or 0.0.0
        project_spec_version = Version.parse(project.version.value)
        if project_spec_version is None or project_spec_version == _default_version:
            project_spec_version = host_project_version

        factory = ExpressionFactory(
            token_resolvers=[
                ("in", input_version),
                ("env", lambda args: os.getenv(args[0]) if args else None),
                ("spec", project_spec_version)
            ],
            default_callback=lambda _key, _args: ""
        )

        for pattern in project_version_patterns:
            condition_pattern, version_pattern = _split_version_pattern(pattern)
            if condition_pattern is not None and not _validate_and_match_condition(io, factory, condition_pattern):
                continue

            resolved_tuple = _resolve_version_from_pattern(io, factory, version_pattern, _default_version, pinning_rule)
            if resolved_tuple:
                resolved, matched_pattern = resolved_tuple
                result[str(project.path)] = resolved
                if io.is_verbose():
                    io.write_line(f"  - Version: <fg=green>{resolved.version}</> (Pattern: '<fg=cyan>{matched_pattern}</>', Pinning rule: <fg=cyan>{pinning_rule.value}</>)")
                else:
                    io.write_line(f"  - Version: <fg=green>{resolved.version}</>")
            break  # Stop after the first matching pattern

    return result


def _resolve_wildcard_constraint(
    dep_name: Optional[str],
    constraint: SpecifierSet,
    host_dependencies: dict[str, ProjectDependency],
) -> tuple[SpecifierSet, str, Optional[SpecifierSet]]:
    if dep_name and dep_name in host_dependencies:
        host_constraint = host_dependencies[dep_name].version_constraint
        if host_constraint:
            return host_constraint, "host", host_constraint
        return constraint, "host-no-constraint", None
    return constraint, "not-found", None


def resolve_project_dependencies_versions(io: IO, host_project: Project, filtered_projects: list[Project]) -> dict[str, list[ResolvedDependencyVersion]]:
    result: dict[str, list[ResolvedDependencyVersion]] = {}

    # Build host dependencies lookup by name
    host_dependencies: dict[str, ProjectDependency] = {}
    for dep in host_project.dependencies:
        dep_name = dep.name
        if dep_name and dep.version_constraint:
            host_dependencies[dep_name] = dep

    for project in filtered_projects:
        resolved_deps: list[ResolvedDependencyVersion] = []

        for dep in project.dependencies:
            dependency_label = "Project dependency" if dep.path else "Dependency"
            constraint = dep.version_constraint
            if constraint is None:
                if io.is_debug():
                    io.write_line(f"  - {dependency_label} '<fg=cyan>{dep.name}</>' skipped (no version constraint).")
                continue

            # Check if constraint is "*" (matches any version) - converts to empty SpecifierSet
            if str(constraint) == "":
                resolved_constraint, resolution_method, host_constraint = _resolve_wildcard_constraint(dep.name, constraint, host_dependencies)
                constraint = resolved_constraint
                if io.is_verbose():
                    if host_constraint:
                        io.write_line(f"  - {dependency_label} '<fg=cyan>{dep.name}</>': <fg=green>{constraint}</> (Resolved from <fg=cyan>{resolution_method}</>: <fg=green>{host_constraint}</>)")
                    else:
                        io.write_line(f"  - {dependency_label} '<fg=cyan>{dep.name}</>': <fg=green>{constraint}</> (from <fg=cyan>{resolution_method}</>)")
                else:
                    io.write_line(f"  - {dependency_label} '<fg=cyan>{dep.name}</>': <fg=green>{constraint}</>")
            elif io.is_debug():
                io.write_line(f"  - {dependency_label} '<fg=cyan>{dep.name}</>': <fg=green>{constraint}</> (direct)")

            resolved_deps.append(ResolvedDependencyVersion(dependency=dep, version_constraint=constraint))

        if resolved_deps:
            result[str(project.path)] = resolved_deps

    return result

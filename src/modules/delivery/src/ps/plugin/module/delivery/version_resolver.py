from calendar import c
import os
from typing import Optional

from cleo.io.io import IO

from ps.version import Version
from ps.token_expressions import ExpressionFactory
from ps.plugin.sdk.models import Project

from .delivery_settings import DeliverySettings

_default_version_patterns: list[str] = [
    "[{in}] {in}",
    "[{env:BUILD_VERSION}] {env:BUILD_VERSION}",
    "{spec}"
]


def _split_version_pattern(pattern: str) -> tuple[Optional[str], str]:
    if pattern.startswith("["):
        end_bracket = pattern.find("]")
        if end_bracket != -1:
            condition = pattern[1:end_bracket]
            version = pattern[end_bracket + 1:].lstrip()
            return condition, version
    return None, pattern


def _resolve_versions(io: IO, input_version: Optional[Version], host_project: Project, filtered_projects: list[Project]) -> dict[str, Optional[Version]]:
    result: dict[str, Optional[Version]] = {}
    host_project_delivery_settings = DeliverySettings.model_validate(host_project.plugin_settings.model_dump())
    host_project_version = Version.parse(host_project.defined_version) or Version()
    for project in filtered_projects:
        project_delivery_settings = DeliverySettings.model_validate(project.plugin_settings.model_dump())
        project_version_patterns = project_delivery_settings.version_patterns or host_project_delivery_settings.version_patterns or _default_version_patterns
        factory = ExpressionFactory(
            token_resolvers=[
                ("in", input_version),
                ("env", lambda args: os.getenv(args[0]) if args else None),
                ("spec", Version.parse(project.defined_version) or host_project_version)
            ],
            default_callback=lambda _key, _args: ""  # Return empty string for any unresolved tokens to avoid leaving raw token expressions in the version string.
        )
        for pattern in project_version_patterns:
            condition_pattern, version_pattern = _split_version_pattern(pattern)
            if condition_pattern is not None:
                condition_validation_result = factory.validate_match(condition_pattern)
                if not condition_validation_result.success:
                    if io.is_verbose():
                        io.write_line(f"<comment>Condition '{condition_pattern}' did not match for project '{project.defined_name or project.path.name}'.</comment>")
                    if io.is_debug():
                        for error in condition_validation_result.errors:
                            io.write_line(f"  - {error}")
                    continue
                if not factory.match(condition_pattern):
                    if io.is_verbose():
                        io.write_line(f"<comment>Condition '{condition_pattern}' evaluated to false for project '{project.defined_name or project.path.name}'.</comment>")
                    continue
            version_validation_result = factory.validate_materialize(version_pattern)
            if not version_validation_result.success:
                io.write_line(f"<comment>Version pattern '{version_pattern}' is invalid for project '{project.defined_name or project.path.name}'.</comment>")
                if io.is_debug():
                    for error in version_validation_result.errors:
                        io.write_line(f"  - {error}")
            else:
                raw_version = factory.materialize(version_pattern)
                parsed_version = Version.parse(raw_version)
                if parsed_version is None:
                    io.write_line(
                        f"<comment>Version pattern '{version_pattern}' did not resolve to a valid version "
                        f"for project '{project.defined_name or project.path.name}'. "
                        f"Resolved value: '{raw_version}'</comment>"
                    )
                    result[str(project.path)] = Version()
                else:
                    result[str(project.path)] = parsed_version
            break  # Stop after the first matching pattern

    # Resolve plugin settings
    # plugin_settings = environment.host_project.plugin_settings
    # delivery_settings = DeliverySettings.model_validate(plugin_settings.model_dump(), by_alias=True)
    # version_patterns = delivery_settings.version_patterns or _default_version_patterns
    # resolved_version: Version = _resolve_version(version_patterns, filtered_projects)

    return result

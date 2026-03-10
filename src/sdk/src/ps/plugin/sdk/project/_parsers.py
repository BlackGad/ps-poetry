from pathlib import Path
from typing import Any, Optional
from tomlkit import TOMLDocument, parse
from packaging.requirements import Requirement

from ._models import Project, ProjectDependency, ProjectFeedSource, SourcePriority
from ._toml_value import TomlValue
from ..settings._parsers import parse_plugin_settings_from_document


def parse_name_from_document(document: TOMLDocument) -> TomlValue:
    return TomlValue.locate(document, ["project.name", "tool.poetry.name"])


def parse_version_from_document(document: TOMLDocument) -> TomlValue:
    return TomlValue.locate(document, ["project.version", "tool.poetry.version"])


def parse_dependency(document: TOMLDocument, dep_path: str, name: str, value: Any, group: Optional[str], project_path: Optional[Path] = None) -> Optional[ProjectDependency]:
    location = TomlValue.locate(document, [dep_path])
    if isinstance(value, str):
        return ProjectDependency(
            location=location,
            name=name,
            group=group,
        )
    if isinstance(value, dict):
        local_path = None
        if value.get("path"):
            local_path = Path(value["path"])
            if project_path and not local_path.is_absolute():
                local_path = (project_path.parent / local_path).resolve()
        return ProjectDependency(
            location=location,
            name=name,
            group=group,
            optional=value.get("optional"),
            python=value.get("python"),
            markers=value.get("markers"),
            extras=list(value.get("extras", [])) or None,
            source=value.get("source"),
            path=local_path,
            develop=value.get("develop"),
            url=value.get("url"),
            git=value.get("git"),
            branch=value.get("branch"),
            tag=value.get("tag"),
            rev=value.get("rev"),
        )

    return None


def parse_dependencies_from_document(document: TOMLDocument, project_path: Optional[Path] = None) -> list[ProjectDependency]:
    dependencies = []

    # Support PEP 621 format (array of PEP 508 strings)
    pep621_deps = TomlValue.locate(document, ["project.dependencies"]).value
    if pep621_deps and isinstance(pep621_deps, list):
        for idx, dep_string in enumerate(pep621_deps):
            if not isinstance(dep_string, str):
                continue

            try:
                req = Requirement(dep_string)
                dep_path = f"project.dependencies[{idx}]"
                location = TomlValue.locate(document, [dep_path])

                dependencies.append(ProjectDependency(
                    location=location,
                    name=req.name,
                    extras=list(req.extras) if req.extras else None,
                    markers=str(req.marker) if req.marker else None,
                    group=None,
                ))
            except (ValueError, TypeError):
                # Skip invalid dependency specifications
                continue

    # Support Poetry format (dictionary)
    main_deps = TomlValue.locate(document, ["tool.poetry.dependencies"]).value or {}
    for name, value in main_deps.items():
        if name == "python":
            continue
        dep_path = f"tool.poetry.dependencies.{name}"
        dep = parse_dependency(document, dep_path, name, value, group=None, project_path=project_path)
        if dep:
            dependencies.append(dep)

    groups = TomlValue.locate(document, ["tool.poetry.group"]).value or {}
    for group_name, group_data in groups.items():
        for name, value in group_data.get("dependencies", {}).items():
            dep_path = f"tool.poetry.group.{group_name}.dependencies.{name}"
            dep = parse_dependency(document, dep_path, name, value, group=group_name, project_path=project_path)
            if dep:
                dependencies.append(dep)

    return dependencies


def parse_sources_from_document(document: TOMLDocument) -> list[ProjectFeedSource]:
    sources_value = TomlValue.locate(document, ["tool.poetry.source"]).value
    if not sources_value or not isinstance(sources_value, list):
        return []

    result = []
    for entry in sources_value:
        if not isinstance(entry, dict) or "name" not in entry:
            continue
        priority_raw = entry.get("priority")
        priority = SourcePriority(priority_raw) if priority_raw in SourcePriority._value2member_map_ else None
        result.append(ProjectFeedSource(
            name=entry["name"],
            url=entry.get("url"),
            priority=priority,
        ))
    return result


def parse_project(project_path: Path) -> Optional[Project]:
    project_path = project_path.resolve()
    if project_path.is_dir():
        project_path = project_path / "pyproject.toml"

    if not project_path.exists():
        return None

    with project_path.open('r', encoding='utf-8') as f:
        data = parse(f.read())
    return Project(
        name=parse_name_from_document(data),
        version=parse_version_from_document(data),
        path=project_path,
        document=data,
        dependencies=parse_dependencies_from_document(data, project_path),
        sources=parse_sources_from_document(data),
        plugin_settings=parse_plugin_settings_from_document(data),
    )

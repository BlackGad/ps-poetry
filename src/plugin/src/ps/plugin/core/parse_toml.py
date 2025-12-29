from pathlib import Path
from typing import Any, Optional
from ps.plugin.sdk.models.settings import PluginSettings
from tomlkit import TOMLDocument, parse

from ps.plugin.sdk import Project, ProjectDependency


def get_data(data: dict, path: str, default: Optional[Any] = None) -> Any:
    keys = path.split(".")
    current = data

    for i, key in enumerate(keys):
        if not isinstance(current, dict):
            return default

        if key not in current:
            return default

        current = current[key]

        # If this is the last key, return whatever value we found
        if i == len(keys) - 1:
            return current

    return default


def parse_name_from_document(document: TOMLDocument) -> Optional[str]:
    name = get_data(document, "project.name", None)
    if not name:
        name = get_data(document, "tool.poetry.name", None)
    return name if name else None


def pase_version_from_document(document: TOMLDocument) -> Optional[str]:
    version = get_data(document, "project.version", None)
    if not version:
        version = get_data(document, "tool.poetry.version", None)
    return version if version else None


def parse_dependency(name: str, value: Any, group: Optional[str]) -> Optional[ProjectDependency]:
    if isinstance(value, str):
        return ProjectDependency(
            defined_name=name,
            defined_version=value,
            group=group,
        )
    if isinstance(value, dict):
        version = value.get("version")
        return ProjectDependency(
            defined_name=name,
            defined_version=str(version) if version is not None else None,
            group=group,
            optional=value.get("optional"),
            python=value.get("python"),
            markers=value.get("markers"),
            extras=list(value.get("extras", [])) or None,
            source=value.get("source"),
            path=Path(value["path"]) if value.get("path") else None,
            develop=value.get("develop"),
            url=value.get("url"),
            git=value.get("git"),
            branch=value.get("branch"),
            tag=value.get("tag"),
            rev=value.get("rev"),
        )

    return None


def parse_dependencies_from_document(document: TOMLDocument) -> list[ProjectDependency]:
    dependencies = []

    main_deps = get_data(document, "tool.poetry.dependencies", {})
    for name, value in main_deps.items():
        if name == "python":
            continue
        dep = parse_dependency(name, value, group=None)
        if dep:
            dependencies.append(dep)

    groups = get_data(document, "tool.poetry.group", {})
    for group_name, group_data in groups.items():
        for name, value in group_data.get("dependencies", {}).items():
            dep = parse_dependency(name, value, group=group_name)
            if dep:
                dependencies.append(dep)

    return dependencies


def parse_plugin_settings_from_document(document: TOMLDocument) -> PluginSettings:
    project_toml = document
    settings_section = get_data(project_toml, f"tool.{PluginSettings.NAME}", {})
    return PluginSettings.model_validate(settings_section)


def parse_project(project_path: Path) -> Project:
    if project_path.is_dir():
        project_path = project_path / "pyproject.toml"

    if not project_path.exists():
        raise FileNotFoundError(f"Project file not found at path: {project_path}")

    with project_path.open('r', encoding='utf-8') as f:
        data = parse(f.read())
    return Project(
        defined_name=parse_name_from_document(data),
        defined_version=pase_version_from_document(data),
        path=project_path,
        document=data,
        dependencies=parse_dependencies_from_document(data),
        plugin_settings=parse_plugin_settings_from_document(data),
    )

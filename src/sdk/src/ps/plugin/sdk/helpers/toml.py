from pathlib import Path
from typing import Any, Optional
from tomlkit import TOMLDocument, parse

from ..models import Project, ProjectDependency, PluginSettings, TomlValue


def parse_name_from_document(document: TOMLDocument) -> TomlValue:
    return TomlValue.locate(document, ["project.name", "tool.poetry.name"])


def parse_version_from_document(document: TOMLDocument) -> TomlValue:
    return TomlValue.locate(document, ["project.version", "tool.poetry.version"])


def parse_dependency(name: str, value: Any, group: Optional[str], project_path: Optional[Path] = None) -> Optional[ProjectDependency]:
    if isinstance(value, str):
        return ProjectDependency(
            defined_name=name,
            defined_version=value,
            group=group,
        )
    if isinstance(value, dict):
        version = value.get("version")
        dep_path = None
        if value.get("path"):
            dep_path = Path(value["path"])
            if project_path and not dep_path.is_absolute():
                dep_path = (project_path.parent / dep_path).resolve()
        return ProjectDependency(
            defined_name=name,
            defined_version=str(version) if version is not None else None,
            group=group,
            optional=value.get("optional"),
            python=value.get("python"),
            markers=value.get("markers"),
            extras=list(value.get("extras", [])) or None,
            source=value.get("source"),
            path=dep_path,
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

    main_deps = TomlValue.locate(document, ["tool.poetry.dependencies"]).value or {}
    for name, value in main_deps.items():
        if name == "python":
            continue
        dep = parse_dependency(name, value, group=None, project_path=project_path)
        if dep:
            dependencies.append(dep)

    groups = TomlValue.locate(document, ["tool.poetry.group"]).value or {}
    for group_name, group_data in groups.items():
        for name, value in group_data.get("dependencies", {}).items():
            dep = parse_dependency(name, value, group=group_name, project_path=project_path)
            if dep:
                dependencies.append(dep)

    return dependencies


def parse_plugin_settings_from_document(document: TOMLDocument) -> PluginSettings:
    project_toml = document
    settings_section = TomlValue.locate(project_toml, [f"tool.{PluginSettings.NAME}"]).value
    if settings_section is None:
        return PluginSettings(enabled=False)
    result = PluginSettings.model_validate(settings_section, by_alias=True)
    if result.enabled is None:
        result.enabled = True
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
        plugin_settings=parse_plugin_settings_from_document(data),
    )

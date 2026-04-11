from pathlib import Path

from cleo.io.io import IO

from ..output import DependencyNode, FormattedDeliveryRenderer, ProjectSummary, PublishWave
from ps.plugin.sdk.project import Environment, Project

from ._metadata import ResolvedEnvironmentMetadata


def build_dependency_tree(
    projects: list[Project],
    environment: Environment,
    metadata: ResolvedEnvironmentMetadata,
) -> list[DependencyNode]:
    project_set = {p.path for p in projects}

    def get_deps(project: Project) -> list[Project]:
        return [dep for dep in environment.project_dependencies(project) if dep.path in project_set]

    all_dep_ids = {id(dep) for p in projects for dep in get_deps(p)}
    roots = [p for p in projects if id(p) not in all_dep_ids]

    visited: set[int] = set()

    def _to_node(project: Project) -> DependencyNode:
        name = project.name.value or project.path.name
        meta = metadata.projects.get(project.path)
        version_str = str(meta.version) if meta else "?"
        children: list[DependencyNode] = []
        if id(project) not in visited:
            visited.add(id(project))
            children = [_to_node(dep) for dep in get_deps(project)]
        return DependencyNode(name=name, version=version_str, children=children)

    return [_to_node(root) for root in roots]


def build_publish_waves(
    projects: list[Project],
    environment: Environment,
    metadata: ResolvedEnvironmentMetadata,
) -> list[PublishWave]:
    path_to_project = {p.path: p for p in projects}
    project_set = set(path_to_project.keys())

    def get_dep_paths(project: Project) -> set[Path]:
        return {dep.path for dep in environment.project_dependencies(project) if dep.path in project_set}

    remaining = {id(p) for p in projects}
    done: set[int] = set()
    raw_waves: list[list[Project]] = []
    while remaining:
        wave = [
            p for p in projects
            if id(p) in remaining
            and all(id(path_to_project[dp]) in done for dp in get_dep_paths(p))
        ]
        if not wave:
            wave = [p for p in projects if id(p) in remaining]
        raw_waves.append(wave)
        for p in wave:
            remaining.discard(id(p))
            done.add(id(p))

    result: list[PublishWave] = []
    for wave_idx, wave in enumerate(raw_waves, 1):
        wave_projects: list[ProjectSummary] = []
        for project in wave:
            name = project.name.value or project.path.name
            meta = metadata.projects.get(project.path)
            version_str = str(meta.version) if meta else "?"
            wave_projects.append(ProjectSummary(name=name, version=version_str, deliver=""))
        result.append(PublishWave(index=wave_idx, projects=wave_projects))
    return result


def log_dependency_tree(
    io: IO,
    projects: list[Project],
    environment: Environment,
    metadata: ResolvedEnvironmentMetadata,
    title: str = "Dependency tree",
) -> None:
    renderer = FormattedDeliveryRenderer(io)
    nodes = build_dependency_tree(projects, environment, metadata)
    renderer.render_dependency_tree(title, nodes)


def log_resolution(
    io: IO,
    metadata: ResolvedEnvironmentMetadata,
    title: str = "Version resolution",
) -> None:
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution(title, metadata.resolutions)


def log_publish_waves(
    io: IO,
    projects: list[Project],
    environment: Environment,
    metadata: ResolvedEnvironmentMetadata,
    title: str = "Publish order",
) -> None:
    renderer = FormattedDeliveryRenderer(io)
    waves = build_publish_waves(projects, environment, metadata)
    renderer.render_publish_waves(title, waves)

import graphlib
from pathlib import Path
from typing import Optional

from cleo.io.io import IO
from poetry.factory import Factory
from poetry.publishing.publisher import Publisher

from ps.plugin.sdk import Project

from .handle_metadata import ResolvedEnvironmentMetadata


def _build_topological_order(
    project_metadata: ResolvedEnvironmentMetadata,
) -> list[Path]:
    graph: dict[Path, set[Path]] = {
        key: {dep.parent for dep in meta.project_dependencies}
        for key, meta in project_metadata.projects.items()
    }
    return list(graphlib.TopologicalSorter(graph).static_order())


def _log_publish_plan(
    io: IO,
    sorted_filtered: list[Project],
    project_metadata: ResolvedEnvironmentMetadata,
    path_to_project: dict[Path, Project],
) -> None:
    show_paths = io.is_verbose()
    resolved_path_to_project = {p.path.resolve(): p for p in path_to_project.values()}

    io.write_line("<fg=magenta>Publish dependency tree:</>")
    for i, project in enumerate(sorted_filtered, 1):
        name = project.name.value or project.path.name
        is_last_project = i == len(sorted_filtered)
        project_prefix = "└── " if is_last_project else "├── "
        path_suffix = f" [<fg=dark_gray>{project.path}</>]" if show_paths else ""
        io.write_line(f"  {project_prefix}<fg=blue>{name}</>{path_suffix}")
        if io.is_debug():
            meta = project_metadata.projects.get(project.path)
            if meta:
                child_indent = "    " if is_last_project else "│   "
                deps = meta.project_dependencies
                for j, dep_toml in enumerate(deps):
                    dep = resolved_path_to_project.get(dep_toml)
                    dep_name = (dep.name.value or dep.path.name) if dep else dep_toml.parent.name
                    dep_prefix = "└── " if j == len(deps) - 1 else "├── "
                    io.write_line(f"  {child_indent}{dep_prefix}<fg=dark_gray>{dep_name}</>")


def publish_projects(
    io: IO,
    filtered_projects: list[Project],
    project_metadata: ResolvedEnvironmentMetadata,
    repository: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    cert: Optional[Path] = None,
    client_cert: Optional[Path] = None,
    dist_dir: Optional[Path] = None,
    dry_run: bool = False,
    skip_existing: bool = False,
) -> int:
    path_to_project = {p.path: p for p in filtered_projects}
    full_order = _build_topological_order(project_metadata)
    sorted_filtered = [path_to_project[k] for k in full_order if k in path_to_project]

    _log_publish_plan(io, sorted_filtered, project_metadata, path_to_project)

    for project in sorted_filtered:
        io.write_line(f"<fg=magenta>Publishing:</> <fg=blue>{project.name.value or project.path.name}</> [<fg=dark_gray>{project.path}</>]")

        poetry_project = Factory().create_poetry(cwd=project.path, io=io)
        publisher = Publisher(poetry_project, io, dist_dir=dist_dir)
        publisher.publish(
            repository_name=repository,
            username=username,
            password=password,
            cert=cert,
            client_cert=client_cert,
            dry_run=dry_run,
            skip_existing=skip_existing,
        )

    return 0

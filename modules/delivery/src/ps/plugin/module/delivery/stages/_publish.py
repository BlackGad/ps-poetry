from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cleo.io.buffered_io import BufferedIO
from cleo.io.io import IO
from poetry.factory import Factory
from poetry.publishing.publisher import Publisher

from ps.plugin.sdk.project import Environment, Project

from ._logging import log_dependency_tree, log_publish_waves
from ._metadata import ResolvedEnvironmentMetadata
from .._parallelization import run_topological


@dataclass
class _PublishItem:
    project: Project
    repository: Optional[str]
    username: Optional[str]
    password: Optional[str]
    cert: Optional[Path]
    client_cert: Optional[Path]
    dist_dir: Optional[Path]
    dry_run: bool
    skip_existing: bool


def _publish_one(buffered_io: BufferedIO, item: _PublishItem) -> int:
    project_name = item.project.name.value or item.project.path.name
    buffered_io.write_line(f"<fg=magenta>Publishing:</> <fg=blue>{project_name}</> [<fg=dark_gray>{item.project.path}</>]")
    poetry_project = Factory().create_poetry(cwd=item.project.path, io=buffered_io)
    Publisher(poetry_project, buffered_io, dist_dir=item.dist_dir).publish(
        repository_name=item.repository,
        username=item.username,
        password=item.password,
        cert=item.cert,
        client_cert=item.client_cert,
        dry_run=item.dry_run,
        skip_existing=item.skip_existing,
    )
    return 0


def publish_projects(
    io: IO,
    filtered_projects: list[Project],
    environment: Environment,
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
    items = [
        _PublishItem(p, repository, username, password, cert, client_cert, dist_dir, dry_run, skip_existing)
        for p in filtered_projects
    ]
    path_to_item = {item.project.path: item for item in items}
    project_set = set(path_to_item.keys())

    def get_deps(item: _PublishItem) -> list[_PublishItem]:
        return [
            path_to_item[dep.path]
            for dep in environment.project_dependencies(item.project)
            if dep.path in project_set
        ]

    log_dependency_tree(io, filtered_projects, environment, project_metadata)
    log_publish_waves(io, filtered_projects, environment, project_metadata)
    return run_topological(io, items, _publish_one, get_deps)

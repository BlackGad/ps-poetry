from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from cleo.io.buffered_io import BufferedIO
from cleo.io.io import IO
from poetry.factory import Factory
from poetry.publishing.publisher import Publisher

from ps.plugin.sdk import Project

from .handle_metadata import ResolvedEnvironmentMetadata
from .handle_parallelization import run_topological


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


def _log_publish_plan(
    io: IO,
    items: list[_PublishItem],
    get_deps: Callable[["_PublishItem"], list["_PublishItem"]],
) -> None:
    all_dep_ids = {id(dep) for item in items for dep in get_deps(item)}
    roots = [item for item in items if id(item) not in all_dep_ids]

    # --- Dependency tree ---
    printed: set[int] = set()

    def _print_item(item: _PublishItem, prefix: str, child_prefix: str) -> None:
        name = item.project.name.value or item.project.path.name
        io.write_line(f"{prefix}<fg=blue>{name}</>")
        if id(item) not in printed:
            printed.add(id(item))
            deps = get_deps(item)
            for i, dep in enumerate(deps):
                is_last = i == len(deps) - 1
                _print_item(
                    dep,
                    child_prefix + ("└── " if is_last else "├── "),
                    child_prefix + ("    " if is_last else "│   "),
                )

    io.write_line("<fg=magenta>Dependency tree:</>")
    for i, root in enumerate(roots):
        is_last = i == len(roots) - 1
        _print_item(
            root,
            "  " + ("└── " if is_last else "├── "),
            "  " + ("    " if is_last else "│   "),
        )

    # --- Publish order (waves) ---
    remaining = set(id(item) for item in items)
    done: set[int] = set()
    waves: list[list[_PublishItem]] = []
    while remaining:
        wave = [item for item in items if id(item) in remaining and all(id(dep) in done for dep in get_deps(item))]
        waves.append(wave)
        for item in wave:
            remaining.discard(id(item))
            done.add(id(item))

    io.write_line("<fg=magenta>Publish order:</>")
    for wave_idx, wave in enumerate(waves, 1):
        is_last_wave = wave_idx == len(waves)
        wave_prefix = "└── " if is_last_wave else "├── "
        wave_child_prefix = "    " if is_last_wave else "│   "
        io.write_line(f"  {wave_prefix}<fg=magenta>Wave {wave_idx}</>")
        for j, item in enumerate(wave):
            name = item.project.name.value or item.project.path.name
            is_last_item = j == len(wave) - 1
            item_prefix = "└── " if is_last_item else "├── "
            io.write_line(f"  {wave_child_prefix}{item_prefix}<fg=blue>{name}</>")


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
    path_to_item = {item.project.path.parent.resolve(): item for item in items}
    filtered_paths = set(path_to_item.keys())

    def get_deps(item: _PublishItem) -> list[_PublishItem]:
        meta = project_metadata.projects.get(item.project.path)
        if not meta:
            return []
        dep_paths = {dep.parent.resolve() for dep in meta.project_dependencies} & filtered_paths
        return [path_to_item[p] for p in dep_paths]

    _log_publish_plan(io, items, get_deps)
    return run_topological(io, items, _publish_one, get_deps)

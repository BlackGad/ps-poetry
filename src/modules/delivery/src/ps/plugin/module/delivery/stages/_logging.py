from pathlib import Path

from cleo.io.io import IO

from ps.plugin.sdk.project import Project

from ._metadata import ResolvedEnvironmentMetadata


def log_dependency_tree(
    io: IO,
    projects: list[Project],
    metadata: ResolvedEnvironmentMetadata,
    title: str = "Dependency tree",
) -> None:
    path_to_project = {p.path.parent.resolve(): p for p in projects}
    filtered_paths = set(path_to_project.keys())

    def get_deps(project: Project) -> list[Project]:
        meta = metadata.projects.get(project.path)
        if not meta:
            return []
        dep_paths = {dep.parent.resolve() for dep in meta.project_dependencies} & filtered_paths
        return [path_to_project[p] for p in dep_paths]

    all_dep_ids = {id(dep) for p in projects for dep in get_deps(p)}
    roots = [p for p in projects if id(p) not in all_dep_ids]

    printed: set[int] = set()

    def _print_node(project: Project, prefix: str, child_prefix: str) -> None:
        name = project.name.value or project.path.name
        meta = metadata.projects.get(project.path)
        version_str = str(meta.version) if meta else "?"
        io.write_line(f"{prefix}<fg=blue>{name}</> <fg=green>{version_str}</>")
        if id(project) not in printed:
            printed.add(id(project))
            deps = get_deps(project)
            for i, dep in enumerate(deps):
                is_last = i == len(deps) - 1
                _print_node(
                    dep,
                    child_prefix + ("└── " if is_last else "├── "),
                    child_prefix + ("    " if is_last else "│   "),
                )

    io.write_line(f"<fg=magenta>{title}:</>")
    for i, root in enumerate(roots):
        is_last = i == len(roots) - 1
        _print_node(
            root,
            "  " + ("└── " if is_last else "├── "),
            "  " + ("    " if is_last else "│   "),
        )


def log_publish_waves(
    io: IO,
    projects: list[Project],
    metadata: ResolvedEnvironmentMetadata,
    title: str = "Publish order",
) -> None:
    path_to_project = {p.path.parent.resolve(): p for p in projects}
    filtered_paths = set(path_to_project.keys())

    def get_dep_paths(project: Project) -> set[Path]:
        meta = metadata.projects.get(project.path)
        if not meta:
            return set()
        return {dep.parent.resolve() for dep in meta.project_dependencies} & filtered_paths

    remaining = {id(p) for p in projects}
    done: set[int] = set()
    waves: list[list[Project]] = []
    while remaining:
        wave = [
            p for p in projects
            if id(p) in remaining
            and all(id(path_to_project[dp]) in done for dp in get_dep_paths(p))
        ]
        if not wave:
            wave = [p for p in projects if id(p) in remaining]
        waves.append(wave)
        for p in wave:
            remaining.discard(id(p))
            done.add(id(p))

    io.write_line(f"<fg=magenta>{title}:</>")
    for wave_idx, wave in enumerate(waves, 1):
        is_last_wave = wave_idx == len(waves)
        wave_prefix = "└── " if is_last_wave else "├── "
        wave_child_prefix = "    " if is_last_wave else "│   "
        io.write_line(f"  {wave_prefix}<fg=magenta>Wave {wave_idx}</>")
        for j, project in enumerate(wave):
            name = project.name.value or project.path.name
            meta = metadata.projects.get(project.path)
            version_str = str(meta.version) if meta else "?"
            is_last_item = j == len(wave) - 1
            item_prefix = "└── " if is_last_item else "├── "
            io.write_line(f"  {wave_child_prefix}{item_prefix}<fg=blue>{name}</> <fg=green>{version_str}</>")

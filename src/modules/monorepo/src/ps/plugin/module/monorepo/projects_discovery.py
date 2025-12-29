from pathlib import Path
from typing import Optional
from cleo.io.io import IO

from ps.plugin.module.monorepo.monorepo_settings import MonorepoSettings, MonorepoProjectMode
from ps.plugin.core.parse_toml import parse_project
from ps.plugin.sdk import Project


def _find_monorepo_host_project(reference_path: Path) -> Optional[Project]:
    current_path = reference_path.parent

    while current_path != current_path.parent:
        potential_host = current_path / "pyproject.toml"
        if potential_host.exists():
            host_project = parse_project(potential_host)
            monorepo_mode = MonorepoSettings.get_mode(host_project.plugin_settings)
            if monorepo_mode == MonorepoProjectMode.HOST:
                return host_project
        current_path = current_path.parent
    return None


def _discover_monorepo_projects(io: IO, reference_path: Path) -> list[Project]:
    monorepo_host = _find_monorepo_host_project(reference_path)
    if not monorepo_host:
        io.write_line(f"<fg=yellow>No monorepo host project found for {reference_path}</>")
        return []
    result: list[Project] = []
    result.append(monorepo_host)
    for dependency in monorepo_host.dependencies:
        if not dependency.path or dependency.develop is False:
            continue
        result.append(parse_project(dependency.path))
    return result

from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

from cleo.io.io import IO

from ps.version import Version
from ps.plugin.sdk.project import Project, parse_project

from ps.plugin.module.delivery.stages._metadata import (
    ResolvedEnvironmentMetadata,
    resolve_environment_metadata,
)


def make_io() -> IO:
    io = MagicMock(spec=IO)
    io.is_debug.return_value = False
    io.is_verbose.return_value = False
    return io


def make_project(tmp_path: Path, *, name: str = "test-project", version: str = "1.2.3", patterns: Optional[list[str]] = None) -> Optional[Project]:
    content_lines = [
        "[project]",
        f'name = "{name}"',
        f'version = "{version}"',
        "",
        "[tool.poetry.dependencies]",
        'python = "^3.10"',
    ]
    if patterns is not None:
        content_lines += [
            "",
            "[tool.ps-plugin]",
            "version-patterns = [",
        ]
        for p in patterns:
            content_lines.append(f'  "{p}",')
        content_lines.append("]")

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("\n".join(content_lines), encoding="utf-8")
    return parse_project(pyproject)


def resolve(
    tmp_path: Path,
    *,
    input_version: Optional[Version] = None,
    host_version: str = "0.0.0",
    host_patterns: Optional[list[str]] = None,
    project_version: str = "1.2.3",
    project_patterns: Optional[list[str]] = None,
    io: Optional[IO] = None,
) -> ResolvedEnvironmentMetadata:
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    host = make_project(host_dir, name="host-project", version=host_version, patterns=host_patterns)
    project = make_project(project_dir, name="my-project", version=project_version, patterns=project_patterns)

    assert host is not None
    assert project is not None

    return resolve_environment_metadata(io or make_io(), input_version, host, [project])

from pathlib import Path
from typing import Optional

from ps.plugin.sdk.project import parse_project, Project

from ps.plugin.module.delivery.stages._metadata import resolve_environment_metadata

from .conftest import make_io, make_project


def _make_project_with_package_mode(tmp_path: Path, package_mode: Optional[bool]) -> Optional[Project]:
    content_lines = [
        "[project]",
        'name = "test-project"',
        'version = "1.0.0"',
        "",
        "[tool.poetry]",
    ]
    if package_mode is not None:
        content_lines.append(f"package-mode = {'true' if package_mode else 'false'}")
    content_lines += [
        "",
        "[tool.poetry.dependencies]",
        'python = "^3.10"',
    ]
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("\n".join(content_lines), encoding="utf-8")
    return parse_project(pyproject)


def _resolve_deliver(tmp_path: Path, package_mode: Optional[bool]) -> bool:
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    host = make_project(host_dir, name="host-project", version="1.0.0")
    project = _make_project_with_package_mode(project_dir, package_mode)

    assert host is not None
    assert project is not None

    result = resolve_environment_metadata(make_io(), None, host, [project])
    meta = next(iter(result.projects.values()))
    return meta.deliver


def test_deliver_defaults_to_true_when_package_mode_absent(tmp_path):
    assert _resolve_deliver(tmp_path, package_mode=None) is True


def test_deliver_true_when_package_mode_true(tmp_path):
    assert _resolve_deliver(tmp_path, package_mode=True) is True


def test_deliver_false_when_package_mode_false(tmp_path):
    assert _resolve_deliver(tmp_path, package_mode=False) is False

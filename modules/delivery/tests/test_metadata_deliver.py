from pathlib import Path
from typing import Optional

from ps.plugin.sdk.project import Environment, parse_project, Project

from ps.plugin.module.delivery.stages._metadata import DeliverableType, resolve_environment_metadata

from .conftest import make_project, make_resolvers


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


def _make_project_with_deliver_setting(tmp_path: Path, deliver: Optional[bool]) -> Optional[Project]:
    content_lines = [
        "[project]",
        'name = "test-project"',
        'version = "1.0.0"',
        "",
        "[tool.poetry]",
        "",
        "[tool.poetry.dependencies]",
        'python = "^3.10"',
        "",
        "[tool.ps-plugin]",
    ]
    if deliver is not None:
        content_lines.append(f"deliver = {'true' if deliver else 'false'}")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("\n".join(content_lines), encoding="utf-8")
    return parse_project(pyproject)


def _resolve_deliver(tmp_path: Path, package_mode: Optional[bool]) -> DeliverableType:
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    make_project(host_dir, name="host-project", version="1.0.0")
    _make_project_with_package_mode(project_dir, package_mode)

    environment = Environment(host_dir / "pyproject.toml")
    environment.add_project(project_dir / "pyproject.toml")

    result = resolve_environment_metadata(environment, make_resolvers())
    project_path = (project_dir / "pyproject.toml").resolve()
    return result.projects[project_path].deliver


def _resolve_deliver_from_setting(tmp_path: Path, deliver: Optional[bool]) -> DeliverableType:
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    make_project(host_dir, name="host-project", version="1.0.0")
    _make_project_with_deliver_setting(project_dir, deliver)

    environment = Environment(host_dir / "pyproject.toml")
    environment.add_project(project_dir / "pyproject.toml")

    result = resolve_environment_metadata(environment, make_resolvers())
    project_path = (project_dir / "pyproject.toml").resolve()
    return result.projects[project_path].deliver


def test_deliver_defaults_to_enabled_when_package_mode_absent(tmp_path):
    assert _resolve_deliver(tmp_path, package_mode=None) == DeliverableType.ENABLED


def test_deliver_enabled_when_package_mode_true(tmp_path):
    assert _resolve_deliver(tmp_path, package_mode=True) == DeliverableType.ENABLED


def test_deliver_disabled_by_package_mode_when_package_mode_false(tmp_path):
    assert _resolve_deliver(tmp_path, package_mode=False) == DeliverableType.DISABLED_BY_PACKAGE_MODE


def test_deliver_enabled_when_deliver_setting_absent(tmp_path):
    assert _resolve_deliver_from_setting(tmp_path, deliver=None) == DeliverableType.ENABLED


def test_deliver_enabled_when_deliver_setting_true(tmp_path):
    assert _resolve_deliver_from_setting(tmp_path, deliver=True) == DeliverableType.ENABLED


def test_deliver_disabled_by_option_when_deliver_setting_false(tmp_path):
    assert _resolve_deliver_from_setting(tmp_path, deliver=False) == DeliverableType.DISABLED_BY_DELIVERABLE_OPTION


def test_package_mode_false_takes_priority_over_deliver_setting(tmp_path):
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    make_project(host_dir, name="host-project", version="1.0.0")

    content_lines = [
        "[project]",
        'name = "test-project"',
        'version = "1.0.0"',
        "",
        "[tool.poetry]",
        "package-mode = false",
        "",
        "[tool.poetry.dependencies]",
        'python = "^3.10"',
        "",
        "[tool.ps-plugin]",
        "deliver = true",
    ]
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("\n".join(content_lines), encoding="utf-8")

    environment = Environment(host_dir / "pyproject.toml")
    environment.add_project(project_dir / "pyproject.toml")

    result = resolve_environment_metadata(environment, make_resolvers())
    project_path = (project_dir / "pyproject.toml").resolve()
    assert result.projects[project_path].deliver == DeliverableType.DISABLED_BY_PACKAGE_MODE

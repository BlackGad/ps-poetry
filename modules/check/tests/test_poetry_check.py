from pathlib import Path
from unittest.mock import MagicMock, patch

from cleo.io.io import IO

from ps.plugin.sdk.project import parse_project, Project
from ps.plugin.module.check.checks import PoetryCheck


def _make_project(tmp_path: Path, name: str) -> Project:
    proj_dir = tmp_path / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    pyproject = proj_dir / "pyproject.toml"
    pyproject.write_text(
        f'[project]\nname = "{name}"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    return project


def _make_io(*, verbose: bool = False) -> MagicMock:
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = verbose
    io.is_decorated.return_value = False
    return io


def test_poetry_check_name():
    check = PoetryCheck()
    assert check.name == "poetry"


def test_poetry_check_can_check_always_true(tmp_path):
    check = PoetryCheck()
    assert check.can_check([_make_project(tmp_path, "a")]) is True


def test_poetry_check_returns_none_on_success(tmp_path):
    project = _make_project(tmp_path, "valid-proj")
    io = _make_io()
    check = PoetryCheck()

    mock_poetry = MagicMock()
    mock_command = MagicMock()

    with patch("ps.plugin.module.check.checks._poetry_check.Factory") as mock_factory, \
            patch("ps.plugin.module.check.checks._poetry_check.CheckCommand", return_value=mock_command):
        mock_factory.return_value.create_poetry.return_value = mock_poetry
        result = check.check(io, [project], fix=False)
    assert result is None


def test_poetry_check_returns_exception_on_error(tmp_path):
    project = _make_project(tmp_path, "bad-proj")
    io = _make_io()
    check = PoetryCheck()

    with patch("ps.plugin.module.check.checks._poetry_check.Factory") as mock_factory:
        mock_factory.return_value.create_poetry.side_effect = Exception("invalid pyproject.toml")
        result = check.check(io, [project], fix=False)
    assert result is not None
    assert "Poetry check failed" in str(result)


def test_poetry_check_verbose_shows_path(tmp_path):
    project = _make_project(tmp_path, "verbose-proj")
    io = _make_io(verbose=True)
    check = PoetryCheck()

    mock_poetry = MagicMock()
    mock_command = MagicMock()

    with patch("ps.plugin.module.check.checks._poetry_check.Factory") as mock_factory, \
            patch("ps.plugin.module.check.checks._poetry_check.CheckCommand", return_value=mock_command):
        mock_factory.return_value.create_poetry.return_value = mock_poetry
        check.check(io, [project], fix=False)

    lines = [c.args[0] for c in io.write_line.call_args_list]
    assert any(str(project.path) in line for line in lines)


def test_poetry_check_no_projects_returns_none():
    check = PoetryCheck()
    io = _make_io()
    result = check.check(io, [], fix=False)
    assert result is None

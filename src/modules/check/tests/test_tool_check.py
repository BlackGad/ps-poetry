from pathlib import Path
from unittest.mock import MagicMock, patch

from cleo.io.io import IO

from ps.di import DI
from ps.plugin.sdk.project import Environment, Project, parse_project
from ps.plugin.module.check.checks._tool_check import _collect_source_paths
from ps.plugin.module.check.checks import (
    PylintCheck,
    PyrightCheck,
    PytestCheck,
    RuffCheck,
)


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


def _make_io() -> MagicMock:
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    io.is_decorated.return_value = False
    return io


def _make_di(tmp_path: Path) -> DI:
    host_dir = tmp_path / "host"
    host_dir.mkdir(parents=True, exist_ok=True)
    pyproject = host_dir / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "host"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    env = Environment(pyproject)
    di = DI()
    di.register(Environment).factory(lambda: env)
    return di


# ---------------------------------------------------------------------------
# _collect_source_paths
# ---------------------------------------------------------------------------

def test_collect_source_paths_empty():
    assert _collect_source_paths([]) == []


def test_collect_source_paths_single_project(tmp_path):
    project = _make_project(tmp_path, "lib-a")
    result = _collect_source_paths([project])
    assert len(result) == 1
    assert result[0] == project.path.parent


def test_collect_source_paths_deduplicates_parent(tmp_path):
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()
    child_dir = parent_dir / "child"
    child_dir.mkdir()
    (parent_dir / "pyproject.toml").write_text(
        '[project]\nname = "parent"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (child_dir / "pyproject.toml").write_text(
        '[project]\nname = "child"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    parent_proj = parse_project(parent_dir / "pyproject.toml")
    child_proj = parse_project(child_dir / "pyproject.toml")
    assert parent_proj is not None
    assert child_proj is not None
    result = _collect_source_paths([parent_proj, child_proj])
    assert len(result) == 1
    assert result[0] == parent_dir


def test_collect_source_paths_independent_paths(tmp_path):
    p1 = _make_project(tmp_path, "a")
    p2 = _make_project(tmp_path, "b")
    result = _collect_source_paths([p1, p2])
    assert len(result) == 2


# ---------------------------------------------------------------------------
# ToolCheck.can_check
# ---------------------------------------------------------------------------

def test_tool_check_can_check_returns_true_when_tool_found(tmp_path):
    di = _make_di(tmp_path)
    check = RuffCheck(di)
    with patch("shutil.which", return_value="/usr/bin/ruff"):
        assert check.can_check([]) is True


def test_tool_check_can_check_returns_false_when_tool_missing(tmp_path):
    di = _make_di(tmp_path)
    check = RuffCheck(di)
    with patch("shutil.which", return_value=None):
        assert check.can_check([]) is False


# ---------------------------------------------------------------------------
# ToolCheck.check — subprocess
# ---------------------------------------------------------------------------

def test_tool_check_returns_none_on_no_source_paths(tmp_path):
    di = _make_di(tmp_path)
    check = RuffCheck(di)
    io = _make_io()
    result = check.check(io, [], fix=False)
    assert result is None


def test_tool_check_returns_none_on_success(tmp_path):
    di = _make_di(tmp_path)
    project = _make_project(tmp_path, "lib-a")
    check = RuffCheck(di)
    io = _make_io()

    mock_stdout = MagicMock()
    mock_stdout.readline = MagicMock(side_effect=[""])

    mock_process = MagicMock()
    mock_process.stdout = mock_stdout
    mock_process.wait.return_value = None
    mock_process.returncode = 0

    with patch("subprocess.Popen", return_value=mock_process):
        result = check.check(io, [project], fix=False)
    assert result is None


def test_tool_check_returns_exception_on_failure(tmp_path):
    di = _make_di(tmp_path)
    project = _make_project(tmp_path, "lib-a")
    check = RuffCheck(di)
    io = _make_io()

    mock_stdout = MagicMock()
    mock_stdout.readline = MagicMock(side_effect=[""])

    mock_process = MagicMock()
    mock_process.stdout = mock_stdout
    mock_process.wait.return_value = None
    mock_process.returncode = 1

    with patch("subprocess.Popen", return_value=mock_process):
        result = check.check(io, [project], fix=False)
    assert result is not None
    assert "Ruff check failed" in str(result)


def test_tool_check_writes_stdout_to_io(tmp_path):
    di = _make_di(tmp_path)
    project = _make_project(tmp_path, "lib-a")
    check = RuffCheck(di)
    io = _make_io()

    mock_stdout = MagicMock()
    mock_stdout.readline = MagicMock(side_effect=["output line\n", ""])

    mock_process = MagicMock()
    mock_process.stdout = mock_stdout
    mock_process.wait.return_value = None
    mock_process.returncode = 0

    with patch("subprocess.Popen", return_value=mock_process):
        check.check(io, [project], fix=False)
    io.write.assert_called()


# ---------------------------------------------------------------------------
# RuffCheck._build_command
# ---------------------------------------------------------------------------

def test_ruff_build_command(tmp_path):
    di = _make_di(tmp_path)
    check = RuffCheck(di)
    src = tmp_path / "src"
    result = check._build_command([src], fix=False)
    assert result == ["ruff", "check", str(src)]


def test_ruff_build_command_with_fix(tmp_path):
    di = _make_di(tmp_path)
    check = RuffCheck(di)
    src = tmp_path / "src"
    result = check._build_command([src], fix=True)
    assert result == ["ruff", "check", "--fix", str(src)]


def test_ruff_build_command_multiple_paths(tmp_path):
    di = _make_di(tmp_path)
    check = RuffCheck(di)
    path_a = tmp_path / "a"
    path_b = tmp_path / "b"
    result = check._build_command([path_a, path_b], fix=False)
    assert result == ["ruff", "check", str(path_a), str(path_b)]


# ---------------------------------------------------------------------------
# PytestCheck._build_command
# ---------------------------------------------------------------------------

def test_pytest_build_command(tmp_path):
    di = _make_di(tmp_path)
    check = PytestCheck(di)
    src = tmp_path / "src"
    result = check._build_command([src], fix=False)
    assert result == ["pytest", str(src)]


# ---------------------------------------------------------------------------
# PyrightCheck._build_command
# ---------------------------------------------------------------------------

def test_pyright_build_command(tmp_path):
    di = _make_di(tmp_path)
    check = PyrightCheck(di)
    src = tmp_path / "src"
    result = check._build_command([src], fix=False)
    assert result == ["pyright", str(src)]


# ---------------------------------------------------------------------------
# PylintCheck._build_command
# ---------------------------------------------------------------------------

def test_pylint_build_command(tmp_path):
    di = _make_di(tmp_path)
    check = PylintCheck(di)
    src = tmp_path / "src"
    result = check._build_command([src], fix=False)
    assert result == ["pylint", str(src)]

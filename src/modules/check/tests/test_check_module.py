from pathlib import Path
from typing import ClassVar, Optional
from unittest.mock import MagicMock

from cleo.io.io import IO

from ps.plugin.core.di import _DI
from ps.plugin.sdk import (
    ICheck,
    Project,
    parse_project,
)
from ps.plugin.module.check.check_module import _filter_checkers, _perform_checks
from ps.plugin.module.check.check_settings import CheckSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Check(ICheck):
    name: ClassVar[str]
    _can: bool = True
    _error: Optional[Exception] = None

    def can_check(self, projects: list[Project]) -> bool:
        return self._can

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        return self._error


def _make_checker(checker_name: str, *, can: bool = True, error: Optional[Exception] = None) -> type:
    return type(checker_name, (_Check,), {"name": checker_name, "_can": can, "_error": error})


def make_io() -> MagicMock:
    io = MagicMock(spec=IO)
    io.is_debug.return_value = False
    io.is_decorated.return_value = False
    return io


def make_di(io: Optional[MagicMock] = None) -> _DI:
    di = _DI()
    resolved_io = io or make_io()
    di.register(IO).factory(lambda: resolved_io)
    return di


def make_project(tmp_path: Path, name: str = "proj") -> Project:
    pyproject = tmp_path / name / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        f'[project]\nname = "{name}"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    return project


def make_settings(checks: Optional[list[str]] = None) -> CheckSettings:
    return CheckSettings(checks=checks)


# ---------------------------------------------------------------------------
# _filter_checkers
# ---------------------------------------------------------------------------

def test_filter_checkers_no_checks_specified_returns_empty():
    checker_a = _make_checker("a")
    checker_b = _make_checker("b")
    checkers = [checker_a(), checker_b()]
    result = _filter_checkers(checkers, make_settings(), make_io())
    assert [c.name for c in result] == []


def test_filter_checkers_filters_by_explicit_list():
    checker_a = _make_checker("a")
    checker_b = _make_checker("b")
    checker_c = _make_checker("c")
    checkers = [checker_a(), checker_b(), checker_c()]
    result = _filter_checkers(checkers, make_settings(checks=["a", "c"]), make_io())
    assert [c.name for c in result] == ["a", "c"]


def test_filter_checkers_respects_order():
    checker_a = _make_checker("a")
    checker_b = _make_checker("b")
    checker_c = _make_checker("c")
    # available order: a, b, c — settings order: c, a
    checkers = [checker_a(), checker_b(), checker_c()]
    result = _filter_checkers(checkers, make_settings(checks=["c", "a"]), make_io())
    assert [c.name for c in result] == ["c", "a"]


def test_filter_checkers_empty_available_returns_empty():
    result = _filter_checkers([], make_settings(checks=["a"]), make_io())
    assert result == []


def test_filter_checkers_unknown_name_returns_empty():
    checker_a = _make_checker("a")
    checkers = [checker_a()]
    result = _filter_checkers(checkers, make_settings(checks=["unknown"]), make_io())
    assert result == []


# ---------------------------------------------------------------------------
# _perform_checks
# ---------------------------------------------------------------------------

def test_perform_checks_no_checkers_returns_0(tmp_path):
    project = make_project(tmp_path)
    assert _perform_checks(make_di(), [project], [], fix=False, continue_on_error=False) == 0


def test_perform_checks_passing_checker_returns_0(tmp_path):
    project = make_project(tmp_path)
    checker = _make_checker("ok")()
    assert _perform_checks(make_di(), [project], [checker], fix=False, continue_on_error=False) == 0


def test_perform_checks_failing_checker_returns_1(tmp_path):
    project = make_project(tmp_path)
    checker = _make_checker("bad", error=Exception("boom"))()
    assert _perform_checks(make_di(), [project], [checker], fix=False, continue_on_error=False) == 1


def test_perform_checks_skipped_checker_not_counted_as_failure(tmp_path):
    project = make_project(tmp_path)
    checker = _make_checker("skip", can=False, error=Exception("boom"))()
    assert _perform_checks(make_di(), [project], [checker], fix=False, continue_on_error=False) == 0


def test_perform_checks_stops_after_first_failure(tmp_path):
    project = make_project(tmp_path)
    called: list[str] = []

    class _TrackCheck(_Check):
        name: ClassVar[str] = "track"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            called.append(self.name)
            return None

    class _FailCheck(_Check):
        name: ClassVar[str] = "fail"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            called.append(self.name)
            return Exception("boom")

    result = _perform_checks(make_di(), [project], [_FailCheck(), _TrackCheck()], fix=False, continue_on_error=False)
    assert result == 1
    assert "track" not in called


def test_perform_checks_continues_after_failure_with_continue_on_error(tmp_path):
    project = make_project(tmp_path)
    called: list[str] = []

    class _FailCheck(_Check):
        name: ClassVar[str] = "fail"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            called.append(self.name)
            return Exception("boom")

    class _TrackCheck(_Check):
        name: ClassVar[str] = "track"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            called.append(self.name)
            return None

    result = _perform_checks(make_di(), [project], [_FailCheck(), _TrackCheck()], fix=False, continue_on_error=True)
    assert result == 1
    assert "track" in called


def test_perform_checks_with_continue_on_error_returns_1_if_any_fail(tmp_path):
    project = make_project(tmp_path)

    class _FailA(_Check):
        name: ClassVar[str] = "fail-a"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            return Exception("first")

    class _FailB(_Check):
        name: ClassVar[str] = "fail-b"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            return Exception("second")

    result = _perform_checks(make_di(), [project], [_FailA(), _FailB()], fix=False, continue_on_error=True)
    assert result == 1


def test_perform_checks_passes_fix_flag(tmp_path):
    project = make_project(tmp_path)
    received_fix: list[bool] = []

    class _FixCheck(_Check):
        name: ClassVar[str] = "fix-check"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            received_fix.append(fix)
            return None

    _perform_checks(make_di(), [project], [_FixCheck()], fix=True, continue_on_error=False)
    assert received_fix == [True]


def test_perform_checks_passes_all_projects(tmp_path):
    proj_a = make_project(tmp_path, "proj-a")
    proj_b = make_project(tmp_path, "proj-b")
    received: list[list[Project]] = []

    class _RecordCheck(_Check):
        name: ClassVar[str] = "record"

        def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
            received.append(projects)
            return None

    _perform_checks(make_di(), [proj_a, proj_b], [_RecordCheck()], fix=False, continue_on_error=False)
    assert len(received) == 1
    assert len(received[0]) == 2

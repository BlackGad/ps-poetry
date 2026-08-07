import threading
from unittest.mock import MagicMock

from cleo.io.outputs.output import Verbosity

from ps.plugin.module.delivery._parallelization import run_parallel, run_topological


def _make_io() -> MagicMock:
    io = MagicMock()
    io.output.is_decorated.return_value = False
    io.output.verbosity = Verbosity.NORMAL
    return io


# ---------------------------------------------------------------------------
# run_parallel
# ---------------------------------------------------------------------------

def test_run_parallel_all_succeed():
    io = _make_io()

    def fn(buffered_io, item):
        buffered_io.write_line(f"item {item}")
        return 0

    exit_code = run_parallel(io, [1, 2, 3], fn)

    assert exit_code == 0


def test_run_parallel_reports_failure_exit_code():
    io = _make_io()

    def fn(_buffered_io, item):
        return 1 if item == 2 else 0

    exit_code = run_parallel(io, [1, 2, 3], fn)

    assert exit_code == 1


def test_run_parallel_runs_all_items_even_if_one_fails():
    io = _make_io()
    ran: list[int] = []
    lock = threading.Lock()

    def fn(_buffered_io, item):
        with lock:
            ran.append(item)
        return 1 if item == 2 else 0

    run_parallel(io, [1, 2, 3], fn)

    assert sorted(ran) == [1, 2, 3]


def test_run_parallel_captures_exception_as_failure():
    io = _make_io()

    def fn(_buffered_io, _item):
        raise RuntimeError("boom")

    exit_code = run_parallel(io, [1], fn)

    assert exit_code == 1


# ---------------------------------------------------------------------------
# run_topological
# ---------------------------------------------------------------------------

def test_run_topological_runs_dependency_before_dependent():
    io = _make_io()
    a, b, c = "a", "b", "c"
    deps = {a: [], b: [a], c: [b]}
    order: list[str] = []
    lock = threading.Lock()

    def fn(_buffered_io, item):
        with lock:
            order.append(item)
        return 0

    exit_code = run_topological(io, [a, b, c], fn, lambda item: deps[item])

    assert exit_code == 0
    assert order.index(a) < order.index(b) < order.index(c)


def test_run_topological_independent_items_all_run():
    io = _make_io()
    ran: list[str] = []
    lock = threading.Lock()

    def fn(_buffered_io, item):
        with lock:
            ran.append(item)
        return 0

    exit_code = run_topological(io, ["a", "b", "c"], fn, lambda _item: [])

    assert exit_code == 0
    assert sorted(ran) == ["a", "b", "c"]


def test_run_topological_skips_dependents_of_failed_dependency():
    io = _make_io()
    a, b, c = "a", "b", "c"
    deps = {a: [], b: [a], c: [b]}
    ran: list[str] = []
    lock = threading.Lock()

    def fn(_buffered_io, item):
        with lock:
            ran.append(item)
        return 1 if item == a else 0

    exit_code = run_topological(io, [a, b, c], fn, lambda item: deps[item])

    assert exit_code != 0
    # b depends on a (failed) and c depends on b (skipped): neither should
    # actually execute fn, only a does.
    assert ran == [a]


def test_run_topological_independent_branch_still_runs_when_sibling_fails():
    io = _make_io()
    a, b, c = "a", "b", "c"
    # b and c both depend on a, but not on each other.
    deps = {a: [], b: [a], c: [a]}
    ran: list[str] = []
    lock = threading.Lock()

    def fn(_buffered_io, item):
        with lock:
            ran.append(item)
        return 1 if item == a else 0

    exit_code = run_topological(io, [a, b, c], fn, lambda item: deps[item])

    assert exit_code != 0
    # Both b and c depend directly on the failed item a, so both are skipped.
    assert ran == [a]


def test_run_topological_reports_success_when_all_succeed():
    io = _make_io()
    a, b = "a", "b"
    deps = {a: [], b: [a]}

    def fn(_buffered_io, _item):
        return 0

    exit_code = run_topological(io, [a, b], fn, lambda item: deps[item])

    assert exit_code == 0

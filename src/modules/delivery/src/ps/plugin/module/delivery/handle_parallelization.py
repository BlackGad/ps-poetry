import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

from cleo.io.buffered_io import BufferedIO
from cleo.io.io import IO

T = TypeVar("T")

_thread_io: threading.local = threading.local()


class ThreadLocalIOHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        bio: BufferedIO | None = getattr(_thread_io, "io", None)
        if bio is None:
            return
        try:
            msg = self.format(record)
            if record.levelname.lower() in ("warning", "error", "exception", "critical"):
                bio.write_error_line(msg)
            else:
                bio.write_line(msg)
        except Exception:
            self.handleError(record)


def _run_buffered(io: IO, item: T, fn: Callable[[BufferedIO, T], int]) -> tuple[int, str, str]:
    buffered_io = BufferedIO(decorated=io.output.is_decorated())
    buffered_io.set_verbosity(io.output.verbosity)
    _thread_io.io = buffered_io
    try:
        exit_code = fn(buffered_io, item)
    except Exception as e:
        buffered_io.write_error_line(f"<error>{e!s}</error>")
        exit_code = 1
    finally:
        _thread_io.io = None
    return exit_code, buffered_io.fetch_output(), buffered_io.fetch_error()


def _flush(io: IO, out: str, err: str) -> None:
    if out:
        io.write(out)
    if err:
        io.write_error(err)


def _normalize(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def run_parallel(io: IO, items: list[T], fn: Callable[[BufferedIO, T], int]) -> int:
    lock = threading.Lock()
    exit_code = 0

    def _run_and_flush(item: T) -> int:
        result, out, err = _run_buffered(io, item, fn)
        with lock:
            _flush(io, out, err)
        return result

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(_run_and_flush, items))

    for result in results:
        if result != 0:
            exit_code = result

    return exit_code


def run_topological(
    io: IO,
    items: list[T],
    fn: Callable[[BufferedIO, T], int],
    get_deps: Callable[[T], list[T]],
) -> int:
    lock = threading.Lock()
    done_events: dict[int, threading.Event] = {id(item): threading.Event() for item in items}

    def _run_and_flush(item: T) -> int:
        for dep in get_deps(item):
            done_events[id(dep)].wait()
        result, out, err = _run_buffered(io, item, fn)
        with lock:
            _flush(io, _normalize(out), _normalize(err))
        done_events[id(item)].set()
        return result

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(_run_and_flush, item) for item in items]

    exit_code = 0
    for future in futures:
        r = future.result()
        if r != 0:
            exit_code = r
    return exit_code

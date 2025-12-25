from typing import Type, Union
from cleo.io.io import IO


def _get_module_name(obj: Union[Type, object]) -> str:
    cls = obj if isinstance(obj, type) else type(obj)
    return f"{cls.__module__}.{cls.__name__}"


def _log_verbose(io: IO, message: str) -> None:
    if io.is_verbose():
        io.write_line(f"<fg=magenta>PS:</> {message}")


def _log_debug(io: IO, message: str) -> None:
    if io.is_debug():
        io.write_line(f"<fg=dark_gray>PS:</> {message}")

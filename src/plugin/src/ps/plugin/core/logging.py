from cleo.io.io import IO


def _log_verbose(io: IO, message: str) -> None:
    if io.is_verbose():
        io.write_line(f"<fg=magenta>PS:</> {message}")


def _log_debug(io: IO, message: str) -> None:
    if io.is_debug():
        io.write_line(f"<fg=dark_gray>PS:</> {message}")

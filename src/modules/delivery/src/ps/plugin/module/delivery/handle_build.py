import logging
from typing import Any, Optional

from cleo.io.buffered_io import BufferedIO
from cleo.io.io import IO
from poetry.console.logging.io_formatter import IOFormatter
from poetry.console.commands.build import (
    BuildHandler,
    BuildOptions,
)
from poetry.factory import Factory
from poetry.utils.env import EnvManager

from ps.plugin.sdk import Project

from .handle_parallelization import ThreadLocalIOHandler, run_parallel


_THREAD_LOG_HANDLER = ThreadLocalIOHandler()
_THREAD_LOG_HANDLER.setFormatter(IOFormatter())

for _logger_name in (
    "poetry.core.masonry.builders",
):
    _builder_logger = logging.getLogger(_logger_name)
    _builder_logger.addHandler(_THREAD_LOG_HANDLER)
    _builder_logger.propagate = False


def _build_one(io: BufferedIO, item: tuple[Project, BuildOptions]) -> int:
    project, options = item
    project_name = project.name.value or project.path.name
    io.write_line(f"<fg=magenta>Executing: build</> <fg=blue>{project_name}</> [<fg=dark_gray>{project.path}</>]")
    poetry_obj = Factory().create_poetry(cwd=project.path, io=io)
    env = EnvManager(poetry_obj, io=io).get()
    return BuildHandler(poetry=poetry_obj, env=env, io=io).build(options=options)


def build_projects(
    io: IO,
    filtered_projects: list[Project],
    formats: Optional[list[str]] = None,
    clean: bool = False,
    output: str = "dist",
    config_settings: Optional[dict[str, Any]] = None,
) -> int:
    options = BuildOptions(
        clean=clean,
        formats=formats or ["sdist", "wheel"],  # type: ignore[arg-type]
        output=output,
        config_settings=config_settings or {},
    )
    return run_parallel(io, [(project, options) for project in filtered_projects], _build_one)

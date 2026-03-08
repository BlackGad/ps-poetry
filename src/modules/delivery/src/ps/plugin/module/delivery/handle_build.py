from typing import Any, Optional

from cleo.io.io import IO
from poetry.console.commands.build import (
    BuildHandler,
    BuildOptions,
)
from poetry.factory import Factory
from poetry.utils.env import EnvManager

from ps.plugin.sdk import Project


def build_projects(
    io: IO,
    filtered_projects: list[Project],
    formats: Optional[list[str]] = None,
    clean: bool = False,
    output: str = "dist",
    config_settings: Optional[dict[str, Any]] = None,
) -> int:
    if formats is None:
        formats = ["sdist", "wheel"]
    if config_settings is None:
        config_settings = {}

    for project in filtered_projects:
        command_name = "build"
        project_name = project.name.value or project.path.name
        io.write_line(f"<fg=magenta>Executing: {command_name}</> <fg=blue>{project_name}</> [<fg=dark_gray>{project.path}</>]")

        try:
            poetry_obj = Factory().create_poetry(project.path)
            env = EnvManager(poetry_obj, io=io).get()
            handler = BuildHandler(poetry=poetry_obj, env=env, io=io)
            options = BuildOptions(  # type: ignore[call-arg]
                clean=clean,
                formats=formats,  # type: ignore[arg-type]
                output=output,
                config_settings=config_settings,
            )
            exit_code = handler.build(options=options)
            if exit_code != 0:
                return exit_code
        except Exception as e:
            io.write_line(f"<error>{command_name} command failed for project '{project.name.value or project.path.name}': {e!s}</error>")
            return 1

    return 0

from cleo.io.io import IO
from poetry.factory import Factory
from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.builders.wheel import WheelBuilder

from ps.plugin.sdk import Project


def build_projects(io: IO, filtered_projects: list[Project]) -> int:
    for project in filtered_projects:
        command_name = "build"
        project_name = project.name.value or project.path.name
        io.write_line(f"<fg=magenta>Executing: {command_name}</> <fg=blue>{project_name}</> [<fg=dark_gray>{project.path}</>]")

        try:
            poetry_obj = Factory().create_poetry(project.path)
            sdist_builder = SdistBuilder(poetry_obj)
            wheel_builder = WheelBuilder(poetry_obj)
            sdist_path = sdist_builder.build()
            wheel_path = wheel_builder.build()
            io.write_line(f"<fg=green>Built:</> {sdist_path}")
            io.write_line(f"<fg=green>Built:</> {wheel_path}")
        except Exception as e:
            io.write_line(f"<error>{command_name} command failed for project '{project.name.value or project.path.name}': {e!s}</error>")
            return 1

    return 0

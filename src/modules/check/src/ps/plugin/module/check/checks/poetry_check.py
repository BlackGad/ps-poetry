from typing import ClassVar, Optional
from cleo.io.io import IO
from cleo.io.buffered_io import BufferedIO

from poetry.factory import Factory
from poetry.console.commands.check import CheckCommand


from ps.plugin.sdk.project import Project
from ps.plugin.sdk.check import ICheck


class PoetryCheck(ICheck):
    name: ClassVar[str] = "poetry"

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        has_errors = False
        for project in projects:
            project_name = project.name.value or project.path.name
            path_suffix = f" [<fg=dark_gray>{project.path}</>]" if io.is_verbose() else ""
            io.write_line(f"Checking <fg=blue>{project_name}</>{path_suffix}")
            try:
                poetry_project = Factory().create_poetry(cwd=project.path, io=io)
                check_command = CheckCommand()
                check_command.set_poetry(poetry_project)
                # Use BufferedIO to capture output
                buffered_io = BufferedIO(decorated=io.is_decorated())
                check_command.execute(buffered_io)
            except Exception as e:
                io.write_line(f"  <error>{e}</error>")
                has_errors = True
        return Exception("Poetry check failed") if has_errors else None

from typing import ClassVar, Optional
from cleo.io.io import IO

from poetry.factory import Factory
from poetry.console.commands.check import CheckCommand


from ps.plugin.sdk import Project, ICheck


class PoetryCheck(ICheck):
    name: ClassVar[str] = "poetry"

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        errors: list[Exception] = []
        for project in projects:
            project_name = project.name.value or project.path.name
            io.write_line(f"<fg=blue>{project_name}</> [<fg=dark_gray>{project.path}</>]")
            try:
                poetry_project = Factory().create_poetry(cwd=project.path, io=io)
                check_command = CheckCommand()
                check_command.set_poetry(poetry_project)
                result = check_command.execute(io)
                if result != 0:
                    errors.append(Exception(f"Poetry check failed for '{project.name.value}' with exit code {result}"))
            except Exception as e:
                io.write_line(f"<error>{e}</error>")
                errors.append(e)
        return errors[0] if errors else None

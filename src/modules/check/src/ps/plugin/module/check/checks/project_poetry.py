from typing import Optional
from cleo.io.io import IO

from poetry.factory import Factory
from poetry.console.commands.check import CheckCommand


from ps.plugin.sdk import Project
from ..sdk.project_check import IProjectCheck


class ProjectPoetryCheck(IProjectCheck):
    @property
    def name(self) -> str:
        return "poetry"

    def check(self, io: IO, project: Project, fix: bool) -> Optional[Exception]:
        try:
            poetry_project = Factory().create_poetry(cwd=project.path, io=io)
            check_command = CheckCommand()
            check_command.set_poetry(poetry_project)
            result = check_command.execute(io)
            if result != 0:
                return Exception(f"Poetry check failed with exit code {result}")
        except Exception as e:
            io.write_line(f"<error>{e}</error>")
            return e

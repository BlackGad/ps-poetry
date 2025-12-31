import subprocess
from typing import Optional
from cleo.io.io import IO

from ps.plugin.sdk import DI, Project, Environment
from ..sdk.solution_check import ISolutionCheck


class SolutionRuffCheck(ISolutionCheck):
    def __init__(self, di: DI) -> None:
        self._di = di

    @property
    def name(self) -> str:
        return "ruff"

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        environment = self._di.resolve(Environment)
        assert environment is not None

        source_paths = []
        for project in projects:
            source_paths.append(project.path.parent)

        if not source_paths:
            io.write_line("No source paths found to lint.")
            return None

        command = ["ruff", "check"]
        if fix:
            command.append("--fix")
        command.extend([str(path) for path in source_paths])

        io.write_line(f"Running command: {' '.join(command)}")

        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            cwd=environment.working_directory or "."
        )
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                io.write(line)

        process.wait()
        if process.returncode != 0:
            return Exception(f"Ruff check failed with exit code {process.returncode}")
        return None

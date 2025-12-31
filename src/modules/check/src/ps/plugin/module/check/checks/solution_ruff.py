import subprocess
from typing import ClassVar, Optional
from cleo.io.io import IO

from ps.plugin.sdk import DI, Project, Environment, ISolutionCheck


class SolutionRuffCheck(ISolutionCheck):
    name: ClassVar[str] = "ruff"

    def __init__(self, di: DI) -> None:
        self._di = di

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        environment = self._di.resolve(Environment)
        assert environment is not None

        all_paths = sorted(
            {project.path.parent for project in projects},
            key=lambda p: len(p.parts)
        )

        source_paths = []
        for path in all_paths:
            if not any(
                path != parent and path.is_relative_to(parent)
                for parent in source_paths
            ):
                source_paths.append(path)

        if not source_paths:
            io.write_line("No source paths found to lint.")
            return None

        command = ["ruff", "check"]
        if fix:
            command.append("--fix")
        command.extend([str(path) for path in source_paths])

        io.write_line(f"Running command: {' '.join(command)}")
        cwd = environment._host_project.path.parent if environment._host_project is not None else "."
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            cwd=cwd
        )
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                io.write(line)

        process.wait()
        if process.returncode != 0:
            return Exception(f"Ruff check failed with exit code {process.returncode}")
        return None

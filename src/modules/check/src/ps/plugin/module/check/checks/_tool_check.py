import shutil
import subprocess
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from cleo.io.io import IO

from ps.plugin.sdk.check import ICheck
from ps.di import DI
from ps.plugin.sdk.project import Environment, Project


def _collect_source_paths(projects: list[Project]) -> list[Path]:
    all_paths = sorted(
        {project.path.parent for project in projects},
        key=lambda p: len(p.parts),
    )
    source_paths: list[Path] = []
    for path in all_paths:
        if not any(
            path != parent and path.is_relative_to(parent)
            for parent in source_paths
        ):
            source_paths.append(path)
    return source_paths


class ToolCheck(ICheck):
    def __init__(self, di: DI) -> None:
        self._di = di

    def can_check(self, projects: list[Project]) -> bool:
        return shutil.which(self.name) is not None

    @abstractmethod
    def _build_command(self, source_paths: list[Path], fix: bool) -> list[str]: ...

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        environment = self._di.resolve(Environment)
        assert environment is not None

        source_paths = _collect_source_paths(projects)
        if not source_paths:
            io.write_line("No source paths found.")
            return None

        command = self._build_command(source_paths, fix)
        io.write_line(f"Running command: {' '.join(command)}")

        cwd = environment.host_project.path.parent
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=cwd,
        )
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                io.write(line)
        process.wait()
        if process.returncode != 0:
            return Exception(f"{self.name.capitalize()} check failed with exit code {process.returncode}")
        return None

from pathlib import Path
from typing import Iterable
import tempfile
import shutil
import hashlib

from .project import Project
from ..helpers.parse_toml import parse_project


class Environment:
    _host_project: Project
    _projects: dict[Path, Project]
    _backups: dict[Path, Path]

    def __init__(self, entry_project_path: Path):
        self._projects = {}
        self._backups = {}
        self._entry_project = self.add_project(entry_project_path, is_host=True)

    @property
    def host_project(self) -> Project:
        return self._host_project

    @property
    def entry_project(self) -> Project:
        return self._entry_project

    @property
    def projects(self) -> Iterable[Project]:
        return self._projects.values()

    def add_project(self, project_path: Path, is_host: bool = False) -> Project:
        project_path = project_path.resolve()
        if project_path.is_dir():
            project_path = project_path / "pyproject.toml"
        if project_path in self._projects:
            project = self._projects[project_path]
        else:
            project = parse_project(project_path)
            if project is None:
                raise FileNotFoundError(f"Project file not found at path: {project_path}")
            self._projects[project_path] = project
            if is_host:
                self._host_project = project
            for dependency in project.dependencies:
                if dependency.path and dependency.develop is not False:
                    self.add_project(dependency.path)
            if project.plugin_settings.host_project:
                host_project_path = Path(project.path.parent / project.plugin_settings.host_project).resolve()
                if host_project_path.is_dir():
                    host_project_path = host_project_path / "pyproject.toml"
                self.add_project(host_project_path, is_host=True)

        return project

    def backup_projects(self, projects: Iterable[Project]) -> None:
        for project in projects:
            pyproject_path = project.path
            if pyproject_path in self._backups:
                continue

            temp_dir = Path(tempfile.gettempdir())
            path_hash = hashlib.sha256(str(pyproject_path).encode()).hexdigest()[:16]
            backup_path = temp_dir / f"pyproject_backup_{path_hash}.toml"
            shutil.copy2(pyproject_path, backup_path)
            self._backups[pyproject_path] = backup_path

    def restore_projects(self, projects: Iterable[Project]) -> None:
        for project in projects:
            pyproject_path = project.path
            if pyproject_path not in self._backups:
                continue

            backup_path = self._backups[pyproject_path]
            if backup_path.exists():
                shutil.copy2(backup_path, pyproject_path)
                backup_path.unlink()
            del self._backups[pyproject_path]

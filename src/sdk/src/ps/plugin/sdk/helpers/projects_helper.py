from pathlib import Path
from typing import Iterable, Optional
from ..models.project import Project


def filter_projects(inputs: list[str], projects: Iterable[Project]) -> list[Project]:
    def _matches_reference(input: str, project_path: Path, project_name: Optional[str]) -> bool:
        if input == project_name:
            return True
        try:
            return Path(input).resolve().is_relative_to(project_path.parent)
        except ValueError:
            return False

    unique_projects: dict[Path, Project] = {}
    for project in projects:
        unique_projects[project.path] = project

    if not inputs:
        selected_projects = unique_projects
    else:
        selected_projects = dict[Path, Project]()
        sorted_projects = sorted(unique_projects.values(), key=lambda item: len(str(item.path)), reverse=True)
        for ref in inputs:
            for project in sorted_projects:
                if _matches_reference(ref, project.path, project.defined_name):
                    selected_projects[project.path] = project
                    break

    return list(selected_projects.values())

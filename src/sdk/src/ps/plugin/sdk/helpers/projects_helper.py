from pathlib import Path
from typing import Iterable, Optional
from ..models.project import Project


def filter_projects(inputs: list[str], projects: Iterable[Project]) -> list[Project]:
    def _matches_reference(input: str, project_path: Path, project_name: Optional[str]) -> bool:
        if input == project_name:
            return True
        try:
            return Path(input).resolve().is_relative_to(project_path)
        except ValueError:
            return False

    if not inputs:
        selected_projects = projects
    else:
        selected_projects = set[Project]()
        for ref in inputs:
            # Find first matching project by name or path
            for project in sorted(projects, key=lambda item: len(str(item.path)), reverse=True):
                if _matches_reference(ref, project.path, project.defined_name):
                    selected_projects.add(project)
                    break
    return list(selected_projects)

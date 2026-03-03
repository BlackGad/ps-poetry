from typing import ClassVar, Optional
from cleo.io.io import IO

from ps.plugin.sdk import Project, ICheck


class EnvironmentCheck(ICheck):
    name: ClassVar[str] = "environment"

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        errors = self._check_conflicting_sources(projects)

        if errors:
            for error in errors:
                io.write_line(f"<error>{error}</error>")
            return Exception(f"Environment check failed with {len(errors)} error(s)")
        return None

    def _check_conflicting_sources(self, projects: list[Project]) -> list[str]:
        # Group occurrences by source name → {field_value: [project_names]}
        urls: dict[str, dict[Optional[str], list[str]]] = {}
        priorities: dict[str, dict[Optional[str], list[str]]] = {}
        names: dict[str, str] = {}

        for project in projects:
            project_name = project.name.value or str(project.path)
            for source in project.sources:
                key = source.name.lower()
                names.setdefault(key, source.name)
                priority = str(source.priority) if source.priority is not None else None
                urls.setdefault(key, {}).setdefault(source.url, []).append(project_name)
                priorities.setdefault(key, {}).setdefault(priority, []).append(project_name)

        errors = []
        for key in urls.keys() | priorities.keys():
            for field, groups in (("urls", urls.get(key, {})), ("priorities", priorities.get(key, {}))):
                if len(groups) > 1:
                    lines = "\n".join(
                        f"  - '{val}' in {', '.join(f'{p!r}' for p in projs)}"
                        for val, projs in groups.items()
                    )
                    errors.append(f"Source '{names[key]}' has conflicting {field}:\n{lines}")

        return errors

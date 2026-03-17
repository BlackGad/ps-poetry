import ast
import re
import sys
from collections import defaultdict
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, packages_distributions
from importlib.metadata import requires as metadata_requires
from pathlib import Path
from typing import ClassVar, Optional

from cleo.io.io import IO

from ps.plugin.module.check._check import ICheck
from ps.plugin.sdk.project import Environment, Project
from ps.plugin.sdk.toml import TomlValue


def _normalize(name: str) -> str:
    return name.lower().replace("-", "_").replace(".", "_")


def _name_variants(name: str) -> set[str]:
    lower = name.lower()
    return {
        lower,
        lower.replace("-", "_").replace(".", "_"),
        lower.replace("_", "-"),
    }


def _package_entries(project: Project) -> list[dict]:
    value = TomlValue.locate(project.document, ["tool.poetry.packages"]).value
    return [entry for entry in value or [] if isinstance(entry, dict)]


def _get_package_source_dirs(project: Project) -> list[Path]:
    project_dir = project.path.parent
    source_dirs = []

    for entry in _package_entries(project):
        include = entry.get("include")
        if not include:
            continue
        base = project_dir / entry["from"] if entry.get("from") else project_dir
        source_dirs.append((base / include).resolve())

    return source_dirs or [project_dir]


def _collect_imports(source_dirs: list[Path]) -> dict[str, set[tuple[Path, int]]]:
    imports: dict[str, set[tuple[Path, int]]] = defaultdict(set)

    for source_dir in source_dirs:
        for py_file in source_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports[alias.name].add((py_file, node.lineno))
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imports[node.module].add((py_file, node.lineno))

    return imports


def _build_local_module_map(projects: list[Project]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)

    for project in projects:
        dist_name = project.name.value
        if not dist_name:
            continue

        for entry in _package_entries(project):
            include = entry.get("include")
            if include:
                result[include.replace("/", ".").replace("\\", ".")].append(str(dist_name))

    return dict(result)


def _build_project_lookup(projects: list[Project]) -> dict[Path, Project]:
    lookup: dict[Path, Project] = {}
    for project in projects:
        lookup[project.path] = project
        lookup[project.path.parent] = project
    return lookup


def _find_providers(
    module: str,
    local_map: Mapping[str, list[str]],
    dist_map: Mapping[str, list[str]],
) -> Optional[list[str]]:
    parts = module.split(".")
    for size in range(len(parts), 0, -1):
        candidate = ".".join(parts[:size])
        if providers := local_map.get(candidate) or dist_map.get(candidate):
            return providers
    return None


def _collect_pypi_transitive_deps(
    package_name: str,
    cache: dict[str, set[str]],
    in_progress: set[str],
) -> set[str]:
    key = _normalize(package_name)
    if key in cache:
        return cache[key]
    if key in in_progress:
        return set()

    in_progress.add(key)
    names: set[str] = set()

    try:
        reqs = metadata_requires(package_name) or []
    except PackageNotFoundError:
        cache[key] = names
        in_progress.discard(key)
        return names

    for req_str in reqs:
        dep_name = re.split(r"[\s\(\[;><=!]", req_str, maxsplit=1)[0].strip()
        if not dep_name:
            continue
        names.update(_name_variants(dep_name))
        names.update(_collect_pypi_transitive_deps(dep_name, cache, in_progress))

    cache[key] = names
    in_progress.discard(key)
    return names


def _collect_all_dep_names(
    root_project: Project,
    project_lookup: Mapping[Path, Project],
    cache: dict[Path, set[str]],
    pypi_cache: dict[str, set[str]],
    in_progress: Optional[set[Path]] = None,
) -> set[str]:
    if root_project.path in cache:
        return cache[root_project.path]

    in_progress = in_progress or set()
    if root_project.path in in_progress:
        return set()

    in_progress.add(root_project.path)
    names: set[str] = set()
    pypi_in_progress: set[str] = set()

    for dep in root_project.dependencies:
        if dep.name:
            names.update(_name_variants(dep.name))
            if not dep.path:
                names.update(_collect_pypi_transitive_deps(dep.name, pypi_cache, pypi_in_progress))

        if dep.path and (transient := project_lookup.get(dep.path) or project_lookup.get(dep.path / "pyproject.toml")):
            names.update(
                _collect_all_dep_names(
                    transient,
                    project_lookup=project_lookup,
                    cache=cache,
                    pypi_cache=pypi_cache,
                    in_progress=in_progress,
                )
            )

    cache[root_project.path] = names
    in_progress.discard(root_project.path)
    return names


class ImportsCheck(ICheck):
    name: ClassVar[str] = "imports"

    def __init__(self, environment: Environment) -> None:
        self._environment = environment
        self._dep_cache: dict[Path, set[str]] = {}
        self._pypi_cache: dict[str, set[str]] = {}

    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]:
        del fix

        dist_map = packages_distributions()
        stdlib_modules = frozenset(sys.stdlib_module_names)  # type: ignore[attr-defined]
        all_projects = list(self._environment.projects)
        local_map = _build_local_module_map(all_projects)
        project_lookup = _build_project_lookup(all_projects)

        total_errors = 0

        for project in projects:
            imports_map = {
                module: locations
                for module, locations in _collect_imports(_get_package_source_dirs(project)).items()
                if module.split(".")[0] not in stdlib_modules and module.split(".")[0] != "__future__"
            }

            project_own_names = _name_variants(str(project.name.value)) | {_normalize(str(project.name.value))}
            dep_names = _collect_all_dep_names(
                project,
                project_lookup=project_lookup,
                cache=self._dep_cache,
                pypi_cache=self._pypi_cache,
            )

            missing: dict[str, set[tuple[Path, int]]] = defaultdict(set)

            for module, locations in sorted(imports_map.items()):
                providers = _find_providers(module, local_map, dist_map)
                if not providers:
                    continue

                normalized_providers = {_normalize(name) for name in providers}
                if normalized_providers & project_own_names:
                    continue
                if normalized_providers & dep_names:
                    continue

                label = providers[0] if len(providers) == 1 else repr(providers)
                missing[label].update(locations)

            if not missing:
                continue

            total_errors += len(missing)
            io.write_line(f"  <fg=blue>{project.path}</> <fg=dark_gray>({project.name.value})</>")
            for dist_name, locations in sorted(missing.items()):
                io.write_line(f"    <error>missing: {dist_name!r}</error>")
                for py_file, line in sorted(locations):
                    io.write_line(f"      <fg=dark_gray>{py_file}:{line}</>")

        if total_errors == 0:
            io.write_line("Imports check passed with no errors")
            return None

        return Exception(f"Imports check failed with {total_errors} missing distribution(s)")

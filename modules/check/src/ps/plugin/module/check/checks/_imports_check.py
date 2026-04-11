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
from ps.plugin.sdk.project import Environment, Project, normalize_dist_name, dist_name_variants
from ps.plugin.sdk.toml import TomlValue


def _package_entries(project: Project) -> list[dict]:
    value = TomlValue.locate(project.document, ["tool.poetry.packages"]).value
    return [entry for entry in value or [] if isinstance(entry, dict)]


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
    key = normalize_dist_name(package_name)
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
        names.update(dist_name_variants(dep_name))
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
            names.update(dist_name_variants(dep.name))
            if not dep.path:
                names.update(_collect_pypi_transitive_deps(dep.name, pypi_cache, pypi_in_progress))

        resolved = dep.resolved_project_path
        if dep.path and resolved and (transient := project_lookup.get(resolved)):
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
        dist_map = packages_distributions()
        stdlib_modules = frozenset(sys.stdlib_module_names)  # type: ignore[attr-defined]
        all_projects = list(self._environment.projects)
        local_map = _build_local_module_map(all_projects)
        project_lookup = _build_project_lookup(all_projects)
        project_by_dist: dict[str, Project] = {
            normalize_dist_name(str(p.name.value)): p
            for p in all_projects
            if p.name.value
        }

        total_errors = 0

        for project in self._environment.sorted_projects(projects):
            imports_map = {
                module: locations
                for module, locations in _collect_imports(project.source_dirs).items()
                if module.split(".")[0] not in stdlib_modules and module.split(".")[0] != "__future__"
            }

            project_own_names = dist_name_variants(str(project.name.value)) | {normalize_dist_name(str(project.name.value))}
            dep_names = _collect_all_dep_names(
                project,
                project_lookup=project_lookup,
                cache=self._dep_cache,
                pypi_cache=self._pypi_cache,
            )

            missing: dict[tuple[str, ...], set[tuple[Path, int]]] = defaultdict(set)

            for module, locations in sorted(imports_map.items()):
                providers = _find_providers(module, local_map, dist_map)
                if not providers:
                    continue

                normalized_providers = {normalize_dist_name(name) for name in providers}
                if normalized_providers & project_own_names:
                    continue
                if normalized_providers & dep_names:
                    continue

                missing[tuple(providers)].update(locations)

            if not missing:
                continue

            io.write_line(f"  <fg=blue>{project.path}</> <fg=dark_gray>({project.name.value})</>")

            if fix:
                self._apply_fix(io, project, missing, dep_names, project_lookup, project_by_dist)
                self._dep_cache.clear()
            else:
                total_errors += len(missing)
                for providers_key, locations in sorted(missing.items()):
                    label = providers_key[0] if len(providers_key) == 1 else " | ".join(providers_key)
                    io.write_line(f"    <error>missing: {label!r}</error>")
                    for py_file, line in sorted(locations):
                        io.write_line(f"      <fg=dark_gray>{py_file}:{line}</>")

        if total_errors == 0:
            io.write_line("Imports check passed with no errors")
            return None

        io.write_line("<comment>Run with --fix to add missing dependencies automatically.</comment>")
        return Exception(f"Imports check failed with {total_errors} missing distribution(s)")

    def _apply_fix(
        self,
        io: IO,
        project: Project,
        missing: dict[tuple[str, ...], set[tuple[Path, int]]],
        dep_names: set[str],
        project_lookup: dict[Path, Project],
        project_by_dist: dict[str, Project],
    ) -> None:
        choices: list[tuple[tuple[str, ...], str, set[str]]] = []
        for providers_key in missing:
            local_provider = next(
                (p for p in providers_key if project_by_dist.get(normalize_dist_name(p))),
                None,
            )
            chosen = local_provider or providers_key[0]
            local_dep = project_by_dist.get(normalize_dist_name(chosen))
            if local_dep:
                coverage = dist_name_variants(chosen) | _collect_all_dep_names(
                    local_dep, project_lookup, self._dep_cache, self._pypi_cache
                )
            else:
                coverage = dist_name_variants(chosen) | _collect_pypi_transitive_deps(
                    chosen, self._pypi_cache, set()
                )
            choices.append((providers_key, chosen, coverage))

        choices.sort(key=lambda x: len(x[2]), reverse=True)

        newly_covered: set[str] = set()
        for providers_key, chosen, coverage in choices:
            norm = {normalize_dist_name(p) for p in providers_key}
            if norm & (dep_names | newly_covered):
                continue

            newly_covered.update(coverage)

            local_dep = project_by_dist.get(normalize_dist_name(chosen))
            if local_dep:
                project.add_development_dependency(chosen, local_dep.path.parent)
                io.write_line(f"    <info>added (local): {chosen!r}</info>")
            else:
                project.add_dependency(chosen, constraint="*")
                io.write_line(f"    <info>added: {chosen!r}</info>")
        project.save()

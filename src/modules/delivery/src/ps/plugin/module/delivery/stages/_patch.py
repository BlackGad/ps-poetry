from cleo.io.buffered_io import BufferedIO
from cleo.io.io import IO

from ps.version import Version
from ps.plugin.sdk.project import Project

from ._metadata import ResolvedEnvironmentMetadata
from .._parallelization import run_parallel


def _patch_project_version(
        io: IO,
        project: Project,
        projects_metadata: ResolvedEnvironmentMetadata) -> bool:
    updated = False
    current_project_version = Version.parse(project.version.value) if project.version.value else None
    metadata = projects_metadata.projects.get(project.path)
    if metadata and current_project_version != metadata.version:
        io.write_line(f"  - Version: <fg=yellow>{current_project_version}</> -> <fg=green>{metadata.version}</>")
        project.version.set(str(metadata.version))
        updated = True
    elif metadata and io.is_verbose():
        io.write_line(f"<comment>  - Version: no change needed (<fg=cyan>{current_project_version}</>).</comment>")
    return updated


def _patch_project_dependencies(
        io: IO,
        project: Project,
        projects_metadata: ResolvedEnvironmentMetadata) -> bool:
    updated = False
    for dependency in project.dependencies:
        if dependency.path is None:
            continue

        dependency_project_path = dependency.path
        if dependency_project_path.suffix != ".toml":
            dependency_project_path = dependency_project_path / "pyproject.toml"
        dependency_project_path = dependency_project_path.resolve()

        dep_metadata = projects_metadata.projects.get(dependency_project_path)
        if not dep_metadata:
            if io.is_verbose():
                io.write_line(f"<comment>  - Project dependency <fg=cyan>{dependency.name}</>: target project not in filtered set ({dependency_project_path}).</comment>")
            continue

        current_constraint = dependency.version_constraint
        new_constraint = dep_metadata.version.get_constraint(dep_metadata.pinning)
        if current_constraint == new_constraint:
            if io.is_verbose():
                io.write_line(f"<comment>  - Project dependency <fg=cyan>{dependency.name}</>: no change needed (<fg=cyan>{new_constraint}</>).</comment>")
            continue

        io.write_line(f"  - Project dependency <fg=cyan>{dependency.name}</>: <fg=yellow>{current_constraint or 'Auto'}</> -> <fg=green>{new_constraint}</>")
        dependency.update_version(new_constraint)
        updated = True
    return updated


def _patch_third_party_dependencies(
        io: IO,
        project: Project,
        projects_metadata: ResolvedEnvironmentMetadata) -> bool:
    updated = False
    metadata = projects_metadata.projects.get(project.path)
    for resolved_dependency_version in (metadata.dependencies if metadata else []):
        dependency = resolved_dependency_version.dependency
        current_constraint = dependency.version_constraint
        new_constraint = resolved_dependency_version.version_constraint

        if current_constraint == new_constraint:
            if io.is_verbose():
                io.write_line(f"<comment>  - Dependency <fg=cyan>{dependency.name}</>: no change needed (<fg=cyan>{new_constraint}</>).</comment>")
            continue

        io.write_line(f"  - Dependency <fg=cyan>{dependency.name}</>: <fg=yellow>{current_constraint or 'Any'}</> -> <fg=green>{new_constraint}</>")
        dependency.update_version(new_constraint)
        updated = True
    return updated


def _patch_one(
        io: BufferedIO,
        item: tuple[Project, ResolvedEnvironmentMetadata]) -> int:
    project, projects_metadata = item
    project_name = project.name.value or project.path.name
    io.write_line(f"<fg=magenta>Patching project:</> <fg=blue>{project_name}</> [<fg=dark_gray>{project.path}</>]")

    version_updated = _patch_project_version(io, project, projects_metadata)
    project_deps_updated = _patch_project_dependencies(io, project, projects_metadata)
    third_party_deps_updated = _patch_third_party_dependencies(io, project, projects_metadata)

    if not (version_updated or project_deps_updated or third_party_deps_updated):
        io.write_line("  - Project is up to date.")
    project.save()
    return 0


def patch_projects(
        io: IO,
        projects: list[Project],
        projects_metadata: ResolvedEnvironmentMetadata) -> int:
    return run_parallel(io, [(p, projects_metadata) for p in projects], _patch_one)

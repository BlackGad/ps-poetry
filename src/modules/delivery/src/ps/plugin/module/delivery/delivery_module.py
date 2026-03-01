from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.io import IO
from typing import ClassVar, Optional

from cleo.io.inputs.input import Input
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from poetry.console.commands.build import BuildCommand
from poetry.console.commands.publish import PublishCommand
from poetry.factory import Factory
from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.builders.wheel import WheelBuilder
from poetry.console.application import Application

from ps.plugin.module.delivery.version_resolver import ResolvedDependencyVersion, resolve_project_dependencies_versions, resolve_project_versions, ResolvedProjectVersion
from ps.version import Version
from ps.plugin.sdk.models import Environment, Project
from ps.plugin.sdk.protocols import (
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    NameAwareProtocol,
)
from ps.plugin.sdk.interfaces import DI
from ps.plugin.sdk.helpers import ensure_argument, ensure_option, filter_projects

BUILD_VERSION_OPTION = "build-version"
BUILD_VERSION_OPTION_SHORT = "b"
INPUTS_ARGUMENT = "inputs"


def _get_inputs(input: Input) -> list[str]:
    return input.arguments.get(INPUTS_ARGUMENT, [])


def _get_version_option(input: Input) -> Optional[str]:
    return input.options.get(BUILD_VERSION_OPTION, None)


def _patch_project_version(
        io: IO,
        project: Project,
        project_versions: dict[str, ResolvedProjectVersion]) -> bool:
    updated = False
    current_project_version = Version.parse(project.version.value) if project.version.value else None
    resolved_project_version = project_versions.get(str(project.path))
    if resolved_project_version and current_project_version != resolved_project_version.version:
        io.write_line(f"  - Version: <fg=yellow>{current_project_version}</> -> <fg=green>{resolved_project_version.version}</>")
        project.version.set(str(resolved_project_version.version))
        updated = True
    elif resolved_project_version and io.is_verbose():
        io.write_line(f"<comment>  - Version: no change needed (<fg=cyan>{current_project_version}</>).</comment>")
    return updated


def _patch_project_dependencies(
        io: IO,
        project: Project,
        project_versions: dict[str, ResolvedProjectVersion]) -> bool:
    updated = False
    for dependency in project.dependencies:
        if dependency.path is None:
            continue

        dependency_project_path = dependency.path
        if dependency_project_path.suffix != ".toml":
            dependency_project_path = dependency_project_path / "pyproject.toml"
        dependency_project_path = dependency_project_path.resolve()

        resolved_dependency_project_version = project_versions.get(str(dependency_project_path))
        if not resolved_dependency_project_version:
            if io.is_verbose():
                io.write_line(f"<comment>  - Project dependency <fg=cyan>{dependency.name}</>: target project not in filtered set ({dependency_project_path}).</comment>")
            continue

        current_constraint = dependency.version_constraint
        new_constraint = resolved_dependency_project_version.version.get_constraint(resolved_dependency_project_version.pinning)
        if current_constraint == new_constraint:
            if io.is_verbose():
                io.write_line(f"<comment>  - Project dependency <fg=cyan>{dependency.name}</>: no change needed (<fg=cyan>{new_constraint}</>).</comment>")
            continue

        io.write_line(f"  - Project dependency <fg=cyan>{dependency.name}</>: <fg=yellow>{current_constraint or '*'}</> -> <fg=green>{new_constraint}</>")
        dependency.update_version(new_constraint)
        updated = True
    return updated


def _patch_third_party_dependencies(
        io: IO,
        project: Project,
        project_dependency_versions: dict[str, list[ResolvedDependencyVersion]]) -> bool:
    updated = False
    for resolved_dependency_version in project_dependency_versions.get(str(project.path), []):
        dependency = resolved_dependency_version.dependency
        current_constraint = dependency.version_constraint
        new_constraint = resolved_dependency_version.version_constraint

        if current_constraint == new_constraint:
            if io.is_verbose():
                io.write_line(f"<comment>  - Dependency <fg=cyan>{dependency.name}</>: no change needed (<fg=cyan>{new_constraint}</>).</comment>")
            continue

        io.write_line(f"  - Dependency <fg=cyan>{dependency.name}</>: <fg=yellow>{current_constraint or '*'}</> -> <fg=green>{new_constraint}</>")
        dependency.update_version(new_constraint)
        updated = True
    return updated


def _patch_project(
        io: IO,
        project: Project,
        project_versions: dict[str, ResolvedProjectVersion],
        project_dependency_versions: dict[str, list[ResolvedDependencyVersion]]) -> None:
    project_name = project.name.value or project.path.name
    io.write_line(f"<fg=cyan>Patching project:</> <fg=cyan>{project_name}</> [<fg=dark_gray>{project.path}</>]")

    version_updated = _patch_project_version(io, project, project_versions)
    project_deps_updated = _patch_project_dependencies(io, project, project_versions)
    third_party_deps_updated = _patch_third_party_dependencies(io, project, project_dependency_versions)

    if not (version_updated or project_deps_updated or third_party_deps_updated):
        io.write_line("  - Project is up to date.")


def _build_projects(io: IO, filtered_projects: list[Project]) -> int:
    for project in filtered_projects:
        command_name = "build"
        io.write_line(f"<fg=blue>Executing: {command_name}</> [<comment>{project.path}</>]")

        try:
            poetry_obj = Factory().create_poetry(project.path)
            sdist_builder = SdistBuilder(poetry_obj)
            wheel_builder = WheelBuilder(poetry_obj)
            sdist_path = sdist_builder.build()
            wheel_path = wheel_builder.build()
            io.write_line(f"<fg=green>Built:</> {sdist_path}")
            io.write_line(f"<fg=green>Built:</> {wheel_path}")
        except Exception as e:
            io.write_line(f"<error>{command_name} command failed for project '{project.name.value or project.path.name}': {e!s}</error>")
            return 1

    return 0


def _publish_projects(io: IO, filtered_projects: list[Project]) -> int:
    for project in filtered_projects:
        command_name = "publish"
        io.write_line(f"<fg=blue>Executing: {command_name}</> [<comment>{project.path}</>]")

        poetry_project = Factory().create_poetry(cwd=project.path, io=io)
        cmd = PublishCommand()
        cmd.set_poetry(poetry_project)
        exit_code = cmd.execute(io)

        if exit_code != 0:
            io.write_line(f"<error>{command_name} command failed for project '{project.name.value or project.path.name}'</error>")
            return exit_code

    return 0


class DeliveryModule(
    NameAwareProtocol,
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol
):
    name: ClassVar[str] = "ps-delivery"

    def __init__(self, di: DI) -> None:
        self._di = di
        self._exit_code: Optional[int] = None

    def handle_activate(self, application: Application) -> bool:
        # Extend the BuildCommand with an optional "inputs" argument
        ensure_argument(BuildCommand, Argument(
            name=INPUTS_ARGUMENT,
            description="Optional inputs pointers to build. It could be project names or paths. If not provided, all discovered projects will be built.",
            is_list=True,
            required=False)
        )
        ensure_option(BuildCommand, Option(
            name=BUILD_VERSION_OPTION,
            description="Specify the version to build the project with.",
            shortcut=BUILD_VERSION_OPTION_SHORT,
            flag=False)
        )
        ensure_argument(PublishCommand, Argument(
            name=INPUTS_ARGUMENT,
            description="Optional inputs pointers to publish. It could be project names or paths. If not provided, all discovered projects will be published.",
            is_list=True,
            required=False)
        )
        ensure_option(PublishCommand, Option(
            name=BUILD_VERSION_OPTION,
            description="Specify the version to publish the project with.",
            shortcut=BUILD_VERSION_OPTION_SHORT,
            flag=False)
        )
        return True

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if not isinstance(event.command, (BuildCommand, PublishCommand)):
            return

        # Disable the original command execution
        event.disable_command()

        environment = self._di.resolve(Environment)
        assert environment is not None

        # Filter projects based on inputs
        inputs = _get_inputs(event.io.input)
        # In case no inputs are provided, and the entry project is different from the host project, add the entry project path as input
        if not inputs and environment.host_project != environment.entry_project:
            inputs.append(str(environment.entry_project.path))

        filtered_projects = filter_projects(inputs, environment.projects)
        if not filtered_projects:
            event.io.write_line("<comment>No projects found to process.</comment>")
            return

        input_version = Version.parse(_get_version_option(event.io.input))
        project_versions = resolve_project_versions(
            event.io,
            input_version,
            environment.host_project,
            environment.projects)
        project_dependency_versions = resolve_project_dependencies_versions(
            event.io,
            environment.host_project,
            filtered_projects)
        try:
            environment.backup_projects(filtered_projects)

            # Patch all projects
            for project in filtered_projects:
                _patch_project(event.io, project, project_versions, project_dependency_versions)
                project.save()

            # Execute build or publish command
            is_publish = isinstance(event.command, PublishCommand)
            if is_publish:
                self._exit_code = _publish_projects(event.io, filtered_projects)
            else:
                self._exit_code = _build_projects(event.io, filtered_projects)
        finally:
            environment.restore_projects(environment.projects)

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if self._exit_code is None:
            return
        event.set_exit_code(self._exit_code)

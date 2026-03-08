from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from pathlib import Path
from typing import ClassVar, Optional

from cleo.io.inputs.input import Input
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from poetry.console.commands.build import BuildCommand
from poetry.console.commands.publish import PublishCommand
from poetry.console.application import Application

from ps.version import Version
from ps.plugin.sdk import (
    Environment,
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    NameAwareProtocol,
    DI,
    ensure_argument,
    ensure_option,
    filter_projects,
)

from .handle_metadata import resolve_environment_metadata, ResolvedProjectMetadata
from .handle_projects_patch import patch_projects
from .handle_build import build_projects
from .handle_publish import publish_projects


BUILD_VERSION_OPTION = "build-version"
BUILD_VERSION_OPTION_SHORT = "b"
INPUTS_ARGUMENT = "inputs"


def _get_inputs(input: Input) -> list[str]:
    return input.arguments.get(INPUTS_ARGUMENT, [])


def _get_version_option(input: Input) -> Optional[str]:
    return input.options.get(BUILD_VERSION_OPTION, None)


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

        input_version = Version.parse(_get_version_option(event.io.input))
        projects_metadata = resolve_environment_metadata(
            event.io,
            input_version,
            environment.host_project,
            environment.projects)

        filtered_projects = filter_projects(inputs, environment.projects)
        excluded = {id(p) for p in filtered_projects if not (projects_metadata.projects.get(p.path) or ResolvedProjectMetadata()).deliver}
        event.io.write_line("<fg=magenta>Delivery scope:</>")
        for p in filtered_projects:
            name = p.name.value or p.path.name
            if id(p) in excluded:
                event.io.write_line(f"  - <fg=dark_gray>{name} (not marked for delivery)</>")
            else:
                event.io.write_line(f"  - <fg=blue>{name}</>")
        filtered_projects = [p for p in filtered_projects if id(p) not in excluded]
        if not filtered_projects:
            event.io.write_line("<comment>No projects found to process.</comment>")
            return

        try:
            environment.backup_projects(filtered_projects)

            # Patch all projects
            patch_exit_code = patch_projects(event.io, filtered_projects, projects_metadata)
            if patch_exit_code != 0:
                self._exit_code = patch_exit_code
                return

            # Execute build or publish command
            is_publish = isinstance(event.command, PublishCommand)
            if is_publish:
                opts = event.io.input.options
                cert = opts.get("cert")
                client_cert = opts.get("client-cert")
                dist_dir = opts.get("dist-dir")
                self._exit_code = publish_projects(
                    event.io,
                    filtered_projects,
                    projects_metadata,
                    repository=opts.get("repository"),
                    username=opts.get("username"),
                    password=opts.get("password"),
                    cert=Path(cert) if cert else None,
                    client_cert=Path(client_cert) if client_cert else None,
                    dist_dir=Path(dist_dir) if dist_dir else None,
                    dry_run=bool(opts.get("dry-run")),
                    skip_existing=bool(opts.get("skip-existing")),
                )
            else:
                opts = event.io.input.options
                self._exit_code = build_projects(
                    event.io,
                    filtered_projects,
                    formats=BuildCommand._prepare_formats(opts.get("format")),
                    clean=bool(opts.get("clean")),
                    output=opts.get("output") or "dist",
                    config_settings=BuildCommand._prepare_config_settings(
                        local_version=opts.get("local-version"),
                        config_settings=opts.get("config-settings"),
                        io=event.io,
                    ),
                )
        finally:
            environment.restore_projects(environment.projects)

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if self._exit_code is None:
            return
        event.set_exit_code(self._exit_code)

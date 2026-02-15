from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from typing import ClassVar, Optional

from cleo.io.inputs.input import Input
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from poetry.console.commands.build import BuildCommand
from poetry.console.commands.publish import PublishCommand
from poetry.console.application import Application

from ps.plugin.module.delivery.version_resolver import _resolve_versions
from ps.version.version import Version
from ps.plugin.sdk.models import Environment
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
        project_versions = _resolve_versions(event.io, input_version, environment.host_project, filtered_projects)
        print(project_versions)

        # for project in filtered_projects:
        # project.defined_version
        # pass

        # Get the "force version" option
        # version = _get_version_option(event.io.input) or _resolve_version(delivery_settings.version_pattern)

        # self._exit_code = _perform_solution_check(self._di, filtered_projects, solution_checkers, fix)

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if not self._exit_code:
            return
        event.set_exit_code(self._exit_code)

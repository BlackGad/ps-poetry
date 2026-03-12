from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from poetry.console.commands.add import AddCommand
from poetry.console.commands.installer_command import InstallerCommand
from poetry.console.commands.remove import RemoveCommand

from ps.plugin.sdk.project import Environment

from ._command_handler_protocol import CommandHandlerProtocol
from ._monorepo_root import _redirect_to_monorepo_root


class DependenciesCommandHandler(CommandHandlerProtocol):
    @staticmethod
    def can_handle(event: ConsoleCommandEvent, environment: Environment) -> bool:
        if not isinstance(event.command, (AddCommand, RemoveCommand)):
            return False
        return environment.host_project != environment.entry_project

    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    def handle_command(self, event: ConsoleCommandEvent) -> None:
        command = event.command
        assert isinstance(command, InstallerCommand)
        _redirect_to_monorepo_root(command, self._environment, event.io)

    def handle_terminate(self, event: ConsoleTerminateEvent) -> None:
        pass

from typing import Protocol

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent

from ps.plugin.sdk import Environment


class CommandHandlerProtocol(Protocol):
    @staticmethod
    def can_handle(event: ConsoleCommandEvent, environment: Environment) -> bool: ...

    def handle_command(self, event: ConsoleCommandEvent) -> None: ...

    def handle_terminate(self, event: ConsoleTerminateEvent) -> None: ...

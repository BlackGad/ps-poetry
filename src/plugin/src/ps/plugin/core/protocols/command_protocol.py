from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event_dispatcher import EventDispatcher

from .module_protocol import ModuleProtocol


@runtime_checkable
class CommandProtocol(ModuleProtocol, Protocol):
    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

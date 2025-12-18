from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_error_event import ConsoleErrorEvent
from cleo.events.event_dispatcher import EventDispatcher

from .module_protocol import ModuleProtocol


@runtime_checkable
class ErrorProtocol(ModuleProtocol, Protocol):
    def handle_error(self, event: ConsoleErrorEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

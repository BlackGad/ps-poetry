from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher

from .module_protocol import ModuleProtocol


@runtime_checkable
class TerminateProtocol(ModuleProtocol, Protocol):
    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

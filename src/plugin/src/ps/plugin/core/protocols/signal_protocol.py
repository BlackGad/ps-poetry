from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_signal_event import ConsoleSignalEvent
from cleo.events.event_dispatcher import EventDispatcher

from .module_protocol import ModuleProtocol


@runtime_checkable
class SignalProtocol(ModuleProtocol, Protocol):
    def handle_signal(self, event: ConsoleSignalEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

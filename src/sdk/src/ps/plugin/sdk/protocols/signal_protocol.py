from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_signal_event import ConsoleSignalEvent
from cleo.events.event_dispatcher import EventDispatcher


@runtime_checkable
class ListenerSignalProtocol(Protocol):
    def handle_signal(self, event: ConsoleSignalEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

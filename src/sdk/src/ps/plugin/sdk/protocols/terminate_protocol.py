from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher


@runtime_checkable
class ListenerTerminateProtocol(Protocol):
    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

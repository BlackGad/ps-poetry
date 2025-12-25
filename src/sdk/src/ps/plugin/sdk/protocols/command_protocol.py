from typing_extensions import Protocol, runtime_checkable

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event_dispatcher import EventDispatcher


@runtime_checkable
class ListenerCommandProtocol(Protocol):
    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None: ...

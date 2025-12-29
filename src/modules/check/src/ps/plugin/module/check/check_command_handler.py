from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event_dispatcher import EventDispatcher

from ps.plugin.sdk import ListenerCommandProtocol


class CheckCommandHandler(ListenerCommandProtocol):
    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if event:
            pass

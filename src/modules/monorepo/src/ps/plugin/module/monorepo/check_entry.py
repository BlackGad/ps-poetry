from cleo.io.io import IO
from cleo.events.event_dispatcher import EventDispatcher
from cleo.events.console_command_event import ConsoleCommandEvent

from poetry.console.commands.build import BuildCommand


class CheckEntry:
    @staticmethod
    def get_module_name() -> str:
        return "Mono: check"

    def __init__(self, io: IO) -> None:
        self._io = io

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        self._io.write_line(f"Handling command event: {event_name}")

    def can_handle_command(self, event: ConsoleCommandEvent, _: str) -> bool:
        return isinstance(event.command, BuildCommand)

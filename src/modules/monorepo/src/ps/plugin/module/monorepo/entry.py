from cleo.io.io import IO
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher


class Entry:
    @staticmethod
    def get_module_name() -> str:
        return "Monorepo"

    def __init__(self, io: IO) -> None:
        self._io = io
        self._io.write_line("Monorepo module entry initialized")

    def handle_command(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
        self._io.write_line(f"Handling command event: {event_name}")

    def can_handle_command(self, event: Event, event_name: str) -> bool:
        return True

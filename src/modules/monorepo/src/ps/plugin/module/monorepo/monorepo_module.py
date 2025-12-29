from cleo.io.io import IO
from cleo.events.event_dispatcher import EventDispatcher
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent

from poetry.console.application import Application

from ps.plugin.sdk import (
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    DI,
    Project
)

from .monorepo_settings import MonorepoSettings, MonorepoProjectMode


def _log_verbose(io: IO, message: str) -> None:
    if io.is_verbose():
        io.write_line(f"<fg=magenta>Monorepo:</> {message}")


def _log_debug(io: IO, message: str) -> None:
    if io.is_debug():
        io.write_line(f"<fg=dark_gray>Monorepo:</> {message}")


class MonorepoModule(ActivateProtocol, ListenerCommandProtocol, ListenerTerminateProtocol):
    def __init__(self, di: DI) -> None:
        self._di = di

    def handle_activate(self, application: Application) -> bool:
        current_project = self._di.resolve(Project)
        assert current_project is not None
        monorepo_mode = MonorepoSettings.get_mode(current_project.plugin_settings)
        if monorepo_mode == MonorepoProjectMode.DISABLED:
            _log_verbose(self.io, f"<info>Project {current_project.defined_name} is not part of a monorepo.</info>")
            return False

        return True

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        _log_verbose(self.io, f"Handling command event: {event_name}")

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        _log_verbose(self.io, f"Handling terminate event: {event_name}")

    @property
    def io(self) -> IO:
        io = self._di.resolve(IO)
        assert io is not None
        return io

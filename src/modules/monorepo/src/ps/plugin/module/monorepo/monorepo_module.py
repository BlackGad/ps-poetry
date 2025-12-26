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
    PluginSettings,
    Project
)

from .monorepo_settings import MonorepoSettings, MonorepoProjectMode


def _log_verbose(io: IO, message: str) -> None:
    if io.is_verbose():
        io.write_line(f"<fg=magenta>PS:</> {message}")


def _log_debug(io: IO, message: str) -> None:
    if io.is_debug():
        io.write_line(f"<fg=dark_gray>PS:</> {message}")


class MonorepoModule(ActivateProtocol, ListenerCommandProtocol, ListenerTerminateProtocol):
    is_active: bool = False

    def __init__(self, io: IO, settings: PluginSettings, active_project: Project, di: DI) -> None:
        self._di = di
        monorepo_settings = MonorepoSettings.model_validate(settings.model_dump())
        if monorepo_settings.monorepo == MonorepoProjectMode.DISABLED:
            _log_verbose(io, f"<info>Project {active_project.defined_name} is not part of a monorepo.</info>")
            return
        self.is_active = True

    def handle_activate(self, application: Application) -> None:
        io = self._di.resolve(IO)
        assert io is not None
        if not self.is_active:
            _log_debug(io, "Monorepo module disabled.")
            return
        _log_verbose(io, "Monorepo module activated.")

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        io = self._di.resolve(IO)
        assert io is not None
        if not self.is_active:
            _log_debug(io, "Monorepo module disabled.")
            return
        _log_verbose(io, f"Handling command event: {event_name}")

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        io = self._di.resolve(IO)
        assert io is not None
        if not self.is_active:
            _log_debug(io, "Monorepo module disabled.")
            return
        _log_verbose(io, f"Handling terminate event: {event_name}")

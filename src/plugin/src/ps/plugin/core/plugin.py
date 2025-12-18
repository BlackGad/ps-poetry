import sys
from typing import Callable

import cleo.events.console_events
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.console_error_event import ConsoleErrorEvent
from cleo.events.console_signal_event import ConsoleSignalEvent
from cleo.events.event_dispatcher import EventDispatcher
from cleo.events.event import Event
from cleo.io.io import IO
from cleo.io.inputs.argv_input import ArgvInput
from cleo.io.outputs.stream_output import StreamOutput
from cleo.io.outputs.output import Verbosity

from poetry.plugins.application_plugin import ApplicationPlugin
from poetry.console.application import Application
from tomlkit import TOMLDocument

from .settings import PluginSettings
from .modules_handler import ModulesHandler
from .protocols import (
    GlobalSetupProtocol,
    CommandProtocol,
    TerminateProtocol,
    ErrorProtocol,
    SignalProtocol,
)


def _create_standard_io() -> IO:
    output = StreamOutput(sys.stdout, verbosity=Verbosity.DEBUG)  # type: ignore
    error_output = StreamOutput(sys.stderr, verbosity=Verbosity.DEBUG)  # type: ignore
    return IO(ArgvInput(), output, error_output)


def _log_verbose(io: IO, message: str) -> None:
    if io.is_verbose():
        io.write_line(f"<fg=magenta>PS:</> {message}")


def _log_debug(io: IO, message: str) -> None:
    if io.is_debug():
        io.write_line(f"<fg=dark_gray>PS:</> {message}")


class Plugin(ApplicationPlugin):

    def __init__(self):
        super().__init__()

    def activate(self, application: Application) -> None:
        assert application.event_dispatcher is not None

        project_toml: TOMLDocument = application.poetry.pyproject.data
        settings_section = project_toml.get("tool", {}).get(PluginSettings.NAME, {})
        io = getattr(application, "_io", None)
        if io is None:
            # For debugging outside Poetry projects
            io = _create_standard_io()
            application._io = io

        try:
            settings: PluginSettings = PluginSettings.model_validate(settings_section)
            if not settings.enabled:
                _log_verbose(io, f"<fg=yellow>Plugin disabled in configuration in {application.poetry.pyproject.file}</>")
                return
        except Exception as e:
            _log_debug(io, f"<error>Not in a valid poetry project or configuration error: {e}</error>")
            return

        _log_verbose(io, "<info>Starting activation...</info>")
        self._modules_handler = ModulesHandler(io)
        self._modules_handler.instantiate_modules(application)

        global_setup_handlers = self._modules_handler.acquire_protocol_handlers(GlobalSetupProtocol)

        _log_verbose(io, f"<info>Activating {len(global_setup_handlers)} global setup handlers...</info>")
        for handler in global_setup_handlers:
            _log_debug(io, f"Executing global setup for module '{handler.get_module_name()}'...")
            handler.global_setup(application)

        self._register_protocol_listener(application, CommandProtocol, cleo.events.console_events.COMMAND, self.command_event_listener)
        self._register_protocol_listener(application, TerminateProtocol, cleo.events.console_events.TERMINATE, self.terminate_event_listener)
        self._register_protocol_listener(application, ErrorProtocol, cleo.events.console_events.ERROR, self.error_event_listener)
        self._register_protocol_listener(application, SignalProtocol, cleo.events.console_events.SIGNAL, self.signal_event_listener)

        self.poetry = application.poetry
        _log_verbose(io, "<info>Activation complete</info>")

    def command_event_listener(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        assert isinstance(event, ConsoleCommandEvent)
        _log_debug(event.io, f"Processing <comment>{event_name}</comment> event")
        for handler in self._modules_handler.acquire_protocol_handlers(CommandProtocol):
            if not handler.can_handle_command(event, event_name):
                _log_debug(event.io, f"Module <comment>{handler.get_module_name()}</comment> skipped event")
                continue
            _log_verbose(event.io, f"<info>Module <comment>{handler.get_module_name()}</comment> handling event</info>")
            handler.handle_command(event, event_name, dispatcher)

    def terminate_event_listener(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        assert isinstance(event, ConsoleTerminateEvent)
        _log_debug(event.io, f"Processing <comment>{event_name}</comment> event")
        for handler in self._modules_handler.acquire_protocol_handlers(TerminateProtocol):
            if not handler.can_handle_terminate(event, event_name):
                _log_debug(event.io, f"Module <comment>{handler.get_module_name()}</comment> skipped event")
                continue
            _log_verbose(event.io, f"<info>Module <comment>{handler.get_module_name()}</comment> handling event</info>")
            handler.handle_terminate(event, event_name, dispatcher)

    def error_event_listener(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        assert isinstance(event, ConsoleErrorEvent)
        _log_debug(event.io, f"Processing <comment>{event_name}</comment> event")
        for handler in self._modules_handler.acquire_protocol_handlers(ErrorProtocol):
            if not handler.can_handle_error(event, event_name):
                _log_debug(event.io, f"Module <comment>{handler.get_module_name()}</comment> skipped event")
                continue
            _log_verbose(event.io, f"<info>Module <comment>{handler.get_module_name()}</comment> handling event</info>")
            handler.handle_error(event, event_name, dispatcher)

    def signal_event_listener(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        assert isinstance(event, ConsoleSignalEvent)
        _log_debug(event.io, f"Processing <comment>{event_name}</comment> event")
        for handler in self._modules_handler.acquire_protocol_handlers(SignalProtocol):
            if not handler.can_handle_signal(event, event_name):
                _log_debug(event.io, f"Module <comment>{handler.get_module_name()}</comment> skipped event")
                continue
            _log_verbose(event.io, f"<info>Module <comment>{handler.get_module_name()}</comment> handling event</info>")
            handler.handle_signal(event, event_name, dispatcher)

    def _register_protocol_listener(
        self,
        application: Application,
        protocol_type: type,
        event_constant: str,
        listener_method: Callable[[Event, str, EventDispatcher], None]
    ) -> None:
        io = application._io
        event_dispatcher = application.event_dispatcher
        assert io
        assert event_dispatcher

        if not self._modules_handler.is_protocol_managed(protocol_type):
            _log_debug(io, f"No modules implement protocol <comment>{protocol_type.__name__}</comment>; skipping listener registration")
            return

        handlers = self._modules_handler.acquire_protocol_handlers(protocol_type)
        _log_verbose(io, f"Found {len(handlers)} module(s) implementing protocol <comment>{protocol_type.__name__}</comment>")
        module_names = ", ".join(handler.get_module_name() for handler in handlers)
        _log_debug(io, f"Modules implementing <comment>{protocol_type.__name__}</comment>: <warn>{module_names}</warn>")
        event_dispatcher.add_listener(event_constant, listener_method)

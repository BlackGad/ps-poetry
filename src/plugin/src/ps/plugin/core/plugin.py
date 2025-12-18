import sys

import cleo.events.console_events
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
from .logging import _log_debug, _log_verbose


def _create_standard_io() -> IO:
    output = StreamOutput(sys.stdout, verbosity=Verbosity.DEBUG)  # type: ignore
    error_output = StreamOutput(sys.stderr, verbosity=Verbosity.DEBUG)  # type: ignore
    return IO(ArgvInput(), output, error_output)


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
            _log_debug(io, f"Executing global setup for module <comment>{handler.get_module_name()}</comment>...")
            handler.global_setup(application)

        self._register_protocol_listener(application, CommandProtocol, cleo.events.console_events.COMMAND)
        self._register_protocol_listener(application, TerminateProtocol, cleo.events.console_events.TERMINATE)
        self._register_protocol_listener(application, ErrorProtocol, cleo.events.console_events.ERROR)
        self._register_protocol_listener(application, SignalProtocol, cleo.events.console_events.SIGNAL)

        self.poetry = application.poetry
        _log_verbose(io, "<info>Activation complete</info>")

    def _register_protocol_listener(
        self,
        application: Application,
        protocol_type: type,
        event_constant: str
    ) -> None:
        io = application._io
        event_dispatcher = application.event_dispatcher
        assert io
        assert event_dispatcher

        handlers = self._modules_handler.acquire_protocol_handlers(protocol_type)
        if not handlers:
            _log_debug(io, f"No modules implement protocol <comment>{protocol_type.__name__}</comment>; skipping listener registration")
            return
        _log_verbose(io, f"Found <fg=yellow>{len(handlers)}</> module(s) implementing protocol <comment>{protocol_type.__name__}</comment>")
        module_names = ", ".join(handler.get_module_name() for handler in handlers)
        _log_debug(io, f"Modules implementing <comment>{protocol_type.__name__}</comment>: <fg=yellow>{module_names}</>")

        # Get the handle_* method name from the protocol type
        handle_method_name = next((name for name in dir(protocol_type) if name.startswith('handle_')), None)
        if not handle_method_name:
            raise RuntimeError(f"Protocol {protocol_type.__name__} has no handle_* method")

        def _listener(event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
            _log_debug(io, f"Processing <comment>{event_name}</comment> event")
            for handler in handlers:
                _log_verbose(io, f"<info>Module <comment>{handler.get_module_name()}</comment> handling event</info>")
                handle_method = getattr(handler, handle_method_name)
                handle_method(event, event_name, dispatcher)
        event_dispatcher.add_listener(event_constant, _listener)

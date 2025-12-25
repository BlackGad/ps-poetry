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

from ps.plugin.sdk import (
    PluginSettings,
    SetupProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    ListenerErrorProtocol,
    ListenerSignalProtocol,
)
from .di import _DI
from .modules_handler import ModulesHandler
from .logging import _log_debug, _log_verbose, _get_module_name
from .parse_toml import get_data


def _create_standard_io() -> IO:
    output = StreamOutput(sys.stdout, verbosity=Verbosity.DEBUG)  # type: ignore
    error_output = StreamOutput(sys.stderr, verbosity=Verbosity.DEBUG)  # type: ignore
    return IO(ArgvInput(), output, error_output)


class Plugin(ApplicationPlugin):

    def __init__(self):
        super().__init__()

    def activate(self, application: Application) -> None:
        assert application.event_dispatcher is not None

        io = self._ensure_io(application)
        project_toml = application.poetry.pyproject.data
        settings_section = get_data(project_toml, f"tool.{PluginSettings.NAME}", {})

        try:
            settings: PluginSettings = PluginSettings.model_validate(settings_section)
            if not settings.enabled:
                _log_verbose(io, f"<fg=yellow>ps-plugin not enabled or disabled in configuration in {application.poetry.pyproject.file}</>")
                return
        except Exception as e:
            _log_debug(io, f"<error>Not in a valid poetry project or configuration error: {e}</error>")
            return

        _log_verbose(io, "<info>Starting activation</info>")

        di = _DI()
        di.singleton(IO).factory(lambda: io)
        di.singleton(Application).factory(lambda: application)

        modules_handler = ModulesHandler(di)
        modules_handler.instantiate_modules(application)

        global_setup_handlers = modules_handler.acquire_protocol_handlers(SetupProtocol)

        _log_verbose(io, f"<info>Activating {len(global_setup_handlers)} global setup handlers</info>")
        for handler in global_setup_handlers:
            _log_debug(io, f"Executing global setup for module <comment>{_get_module_name(handler)}</comment>")
            handler.global_setup(application)

        protocols_to_register = {
            ListenerCommandProtocol: cleo.events.console_events.COMMAND,
            ListenerTerminateProtocol: cleo.events.console_events.TERMINATE,
            ListenerErrorProtocol: cleo.events.console_events.ERROR,
            ListenerSignalProtocol: cleo.events.console_events.SIGNAL,
        }

        for protocol_type, event_constant in protocols_to_register.items():
            handlers = modules_handler.acquire_protocol_handlers(protocol_type)
            self._register_protocol_listener(
                io,
                application.event_dispatcher,
                protocol_type,
                event_constant,
                handlers)

        self.poetry = application.poetry
        _log_verbose(io, "<info>Activation complete</info>")

    def _register_protocol_listener(
        self,
        io: IO,
        event_dispatcher: EventDispatcher,
        protocol_type: type,
        event_constant: str,
        handlers: list,
    ) -> None:
        if not handlers:
            _log_debug(io, f"No modules implement protocol <comment>{protocol_type.__name__}</comment>; skipping listener registration")
            return
        _log_verbose(io, f"Found <fg=yellow>{len(handlers)}</> module(s) implementing protocol <comment>{protocol_type.__name__}</comment>")
        module_names = ", ".join(_get_module_name(handler) for handler in handlers)
        _log_debug(io, f"Modules implementing <comment>{protocol_type.__name__}</comment>: <fg=yellow>{module_names}</>")

        # Get the handle_* method name from the protocol type
        handle_method_name = next((name for name in dir(protocol_type) if name.startswith('handle_')), None)
        if not handle_method_name:
            raise RuntimeError(f"Protocol {protocol_type.__name__} has no handle_* method")

        def _listener(event: Event, event_name: str, dispatcher: EventDispatcher) -> None:
            _log_debug(io, f"Processing <comment>{event_name}</comment> event")
            for handler in handlers:
                _log_verbose(io, f"<info>Module <comment>{_get_module_name(handler)}</comment> handling event</info>")
                handle_method = getattr(handler, handle_method_name)
                handle_method(event, event_name, dispatcher)
        event_dispatcher.add_listener(event_constant, _listener)

    def _ensure_io(self, application: Application) -> IO:
        io = getattr(application, "_io", None)
        if io is None:
            # For debugging outside Poetry projects
            io = _create_standard_io()
            application._io = io
        return io

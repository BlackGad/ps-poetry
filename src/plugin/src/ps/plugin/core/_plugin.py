import sys

import cleo.events.console_events
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.inputs.argv_input import ArgvInput
from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity
from cleo.io.outputs.stream_output import StreamOutput
from poetry.console.application import Application
from poetry.plugins.application_plugin import ApplicationPlugin

from ps.di import DI
from ps.plugin.sdk.logging import log_debug, log_verbose
from ps.plugin.sdk.project import Environment
from ps.plugin.sdk.settings import PluginSettings, parse_plugin_settings_from_document

from ._modules_handler import _ModulesHandler

_EVENT_LISTENERS = {
    "command": cleo.events.console_events.COMMAND,
    "terminate": cleo.events.console_events.TERMINATE,
    "error": cleo.events.console_events.ERROR,
    "signal": cleo.events.console_events.SIGNAL,
}


def _create_standard_io() -> IO:
    output = StreamOutput(sys.stdout, verbosity=Verbosity.DEBUG)  # type: ignore
    error_output = StreamOutput(sys.stderr, verbosity=Verbosity.DEBUG)  # type: ignore
    return IO(ArgvInput(), output, error_output)


def _resolve_settings(environment: Environment) -> PluginSettings:
    return environment.host_project.plugin_settings


class Plugin(ApplicationPlugin):
    def __init__(self) -> None:
        super().__init__()
        self._di = DI()

    def activate(self, application: Application) -> None:
        assert application.event_dispatcher is not None
        event_dispatcher = application.event_dispatcher

        io = self._ensure_io(application)
        project_toml = application.poetry.pyproject.data
        try:
            settings: PluginSettings = parse_plugin_settings_from_document(project_toml)
            if not settings.enabled:
                log_verbose(io, f"<fg=yellow>ps-plugin not enabled or disabled in configuration in {application.poetry.pyproject.file}</>")
                return
        except Exception as e:
            log_debug(io, f"<error>Not in a valid poetry project or configuration error: {e}</error>")
            return

        log_verbose(io, "<info>Starting activation</info>")

        di = self._di
        di.register(IO).factory(lambda: io)
        di.register(Application).factory(lambda: application)
        di.register(Environment).factory(lambda path: Environment(path), application.poetry.pyproject_path)
        di.register(PluginSettings).factory(_resolve_settings)
        di.register(EventDispatcher).factory(lambda: event_dispatcher)

        handler = di.spawn(_ModulesHandler)
        handler.discover_and_instantiate()
        handler.activate()

        for event_type, event_constant in _EVENT_LISTENERS.items():
            fns = handler.get_event_handlers(event_type)
            if not fns:
                log_debug(io, f"No handlers for <comment>{event_type}</comment>; skipping listener")
                continue
            log_verbose(io, f"Registering <fg=yellow>{len(fns)}</> handler(s) for <comment>{event_type}</comment>")
            self._register_listener(event_dispatcher, di, io, event_type, event_constant, fns)

        self.poetry = application.poetry
        log_verbose(io, "<info>Activation complete</info>")

    def _register_listener(
        self,
        event_dispatcher: EventDispatcher,
        di: DI,
        io: IO,
        event_type: str,
        event_constant: str,
        fns: list,
    ) -> None:
        def _listener(event: Event, event_name: str, dispatcher: EventDispatcher) -> None:  # noqa: ARG001
            with di.scope() as scope:
                scope.register(type(event)).factory(lambda: event)
                log_debug(io, f"Processing <comment>{event_name}</comment> event")
                for fn in fns:
                    scope.satisfy(fn)()
                    if isinstance(event, ConsoleCommandEvent) and not event.command_should_run():
                        log_debug(io, f"Command execution stopped after <comment>{event_type}</comment> handler")
                        break

        event_dispatcher.add_listener(event_constant, _listener)

    def _ensure_io(self, application: Application) -> IO:
        io = getattr(application, "_io", None)
        if io is None:
            io = _create_standard_io()
            application._io = io
        return io

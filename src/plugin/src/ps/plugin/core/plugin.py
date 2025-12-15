import cleo.events.console_events
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from cleo.events.event import Event

from poetry.plugins.application_plugin import ApplicationPlugin
from poetry.console.application import Application


class Plugin(ApplicationPlugin):

    def __init__(self):
        super().__init__()

    def activate(self, application: Application) -> None:
        assert application.event_dispatcher is not None
        application.event_dispatcher.add_listener(
            cleo.events.console_events.COMMAND, self.console_command_event_listener
        )
        application.event_dispatcher.add_listener(
            cleo.events.console_events.TERMINATE, self.post_console_command_event_listener
        )

        self.poetry = application.poetry

    def console_command_event_listener(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        assert isinstance(event, ConsoleCommandEvent)
        event.io.write_line("<info>Plugin: Starting command execution...</info>")

    def post_console_command_event_listener(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        assert isinstance(event, ConsoleTerminateEvent)
        event.io.write_line("<info>Plugin: Command execution finished.</info>")

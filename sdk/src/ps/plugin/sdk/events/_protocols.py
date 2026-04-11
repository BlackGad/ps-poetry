from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_error_event import ConsoleErrorEvent
from cleo.events.console_signal_event import ConsoleSignalEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from poetry.console.application import Application
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class PoetryActivateProtocol(Protocol):
    def poetry_activate(self, application: Application) -> bool: ...


@runtime_checkable
class PoetryCommandProtocol(Protocol):
    def poetry_command(self, event: ConsoleCommandEvent, dispatcher: EventDispatcher) -> None: ...


@runtime_checkable
class PoetryErrorProtocol(Protocol):
    def poetry_error(self, event: ConsoleErrorEvent, dispatcher: EventDispatcher) -> None: ...


@runtime_checkable
class PoetryTerminateProtocol(Protocol):
    def poetry_terminate(self, event: ConsoleTerminateEvent, dispatcher: EventDispatcher) -> None: ...


@runtime_checkable
class PoetrySignalProtocol(Protocol):
    def poetry_signal(self, event: ConsoleSignalEvent, dispatcher: EventDispatcher) -> None: ...

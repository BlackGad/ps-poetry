from typing import Type, List
from typing_extensions import Protocol, runtime_checkable

from poetry.console.application import Application

from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher


@runtime_checkable
class ModuleProtocol(Protocol):
    @staticmethod
    def get_module_name() -> str: ...


@runtime_checkable
class CustomProtocolsProtocol(ModuleProtocol, Protocol):
    @staticmethod
    def declare_custom_protocols() -> List[Type]: ...


@runtime_checkable
class GlobalSetupProtocol(ModuleProtocol, Protocol):
    def global_setup(self, application: Application) -> None: ...


@runtime_checkable
class CommandProtocol(ModuleProtocol, Protocol):
    def handle_command(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None: ...
    def can_handle_command(self, event: Event, event_name: str) -> bool: ...


@runtime_checkable
class TerminateProtocol(ModuleProtocol, Protocol):
    def handle_terminate(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None: ...
    def can_handle_terminate(self, event: Event, event_name: str) -> bool: ...


@runtime_checkable
class ErrorProtocol(ModuleProtocol, Protocol):
    def handle_error(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None: ...
    def can_handle_error(self, event: Event, event_name: str) -> bool: ...


@runtime_checkable
class SignalProtocol(ModuleProtocol, Protocol):
    def handle_signal(self, event: Event, event_name: str, dispatcher: EventDispatcher) -> None: ...
    def can_handle_signal(self, event: Event, event_name: str) -> bool: ...

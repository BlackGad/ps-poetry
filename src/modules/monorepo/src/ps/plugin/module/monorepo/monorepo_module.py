from typing import ClassVar, Type

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher


from ps.plugin.sdk.protocols import (
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    NameAwareProtocol,
)

from ps.plugin.sdk.interfaces import DI
from ps.plugin.sdk.models import Environment

from .command_handler_protocol import CommandHandlerProtocol
from .command_handler_env import EnvCommandHandler
from .command_handler_lock import LockCommandHandler
from .command_handler_dependencies import DependenciesCommandHandler

_command_handlers: list[Type[CommandHandlerProtocol]] = [
    EnvCommandHandler,
    LockCommandHandler,
    DependenciesCommandHandler,
]


class MonorepoModule(
    NameAwareProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol
):
    name: ClassVar[str] = "ps-monorepo"

    def __init__(self, di: DI) -> None:
        self._di = di
        self._handlers: list[CommandHandlerProtocol] = []

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        environment = self._di.resolve(Environment)
        assert environment is not None

        for handler_cls in _command_handlers:
            if not handler_cls.can_handle(event, environment):
                continue
            handler = self._di.spawn(handler_cls)
            self._handlers.append(handler)
            handler.handle_command(event)

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        for handler in reversed(self._handlers):
            handler.handle_terminate(event)

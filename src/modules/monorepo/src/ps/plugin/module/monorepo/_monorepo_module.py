from typing import ClassVar, Optional, Type

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher

from ps.plugin.sdk.di import DI
from ps.plugin.sdk.events import ListenerCommandProtocol, ListenerTerminateProtocol
from ps.plugin.sdk.mixins import NameAwareProtocol
from ps.plugin.sdk.project import Environment

from ._command_handler_dependencies import DependenciesCommandHandler
from ._command_handler_env import EnvCommandHandler
from ._command_handler_lock import LockCommandHandler
from ._command_handler_protocol import CommandHandlerProtocol

_command_handler_types: list[Type[CommandHandlerProtocol]] = [
    EnvCommandHandler,
    LockCommandHandler,
    DependenciesCommandHandler,
]


class MonorepoModule(
    NameAwareProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
):
    name: ClassVar[str] = "ps-monorepo"

    def __init__(self, di: DI) -> None:
        self._di = di
        self._handlers: list[CommandHandlerProtocol] = []
        self._exit_code: Optional[int] = None

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        environment = self._di.resolve(Environment)
        assert environment is not None

        for handler_cls in _command_handler_types:
            if not handler_cls.can_handle(event, environment):
                continue
            handler = self._di.spawn(handler_cls)
            self._handlers.append(handler)
            handler.handle_command(event)

        self._exit_code = 0

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if self._exit_code is None:
            return

        for handler in reversed(self._handlers):
            handler.handle_terminate(event)

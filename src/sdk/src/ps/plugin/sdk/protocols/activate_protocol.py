from typing_extensions import Protocol, runtime_checkable

from poetry.console.application import Application


@runtime_checkable
class ActivateProtocol(Protocol):
    def handle_activate(self, application: Application) -> bool: ...

from typing_extensions import Protocol, runtime_checkable

from poetry.console.application import Application


@runtime_checkable
class SetupProtocol(Protocol):
    def global_setup(self, application: Application) -> None: ...

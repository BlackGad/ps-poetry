from typing_extensions import Protocol, runtime_checkable

from poetry.console.application import Application

from .module_protocol import ModuleProtocol


@runtime_checkable
class GlobalSetupProtocol(ModuleProtocol, Protocol):
    def global_setup(self, application: Application) -> None: ...

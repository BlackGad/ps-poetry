from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class ModuleProtocol(Protocol):
    @staticmethod
    def get_module_name() -> str: ...

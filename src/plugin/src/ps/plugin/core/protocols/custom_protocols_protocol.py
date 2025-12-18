from typing import Type, List
from typing_extensions import Protocol, runtime_checkable

from .module_protocol import ModuleProtocol


@runtime_checkable
class CustomProtocolsProtocol(ModuleProtocol, Protocol):
    @staticmethod
    def declare_custom_protocols() -> List[Type]: ...

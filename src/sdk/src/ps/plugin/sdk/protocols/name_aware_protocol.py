from typing import ClassVar
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class NameAwareProtocol(Protocol):
    name: ClassVar[str]

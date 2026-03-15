from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ..mixins._name_aware_protocol import NameAwareProtocol


class IVersionTokenResolver(NameAwareProtocol, ABC):
    name: ClassVar[str]

    @abstractmethod
    def get_resolver(self) -> Any: ...

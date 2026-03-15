from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ps.plugin.sdk.mixins import NameAwareProtocol


class IVersionTokenResolver(NameAwareProtocol, ABC):
    name: ClassVar[str]

    @abstractmethod
    def get_resolver(self) -> Any: ...

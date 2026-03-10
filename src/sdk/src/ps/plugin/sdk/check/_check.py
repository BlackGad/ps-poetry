from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from cleo.io.io import IO

from ..project._models import Project
from ..mixins._name_aware_protocol import NameAwareProtocol


class ICheck(NameAwareProtocol, ABC):
    name: ClassVar[str]

    def can_check(self, projects: list[Project]) -> bool:
        return True

    @abstractmethod
    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]: ...

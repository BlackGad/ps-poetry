from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from cleo.io.io import IO

from ..models.project import Project
from ..protocols import NameAwareProtocol


class ISolutionCheck(NameAwareProtocol, ABC):
    name: ClassVar[str]

    def can_check(self, projects: list[Project]) -> bool:
        return True

    @abstractmethod
    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]: ...

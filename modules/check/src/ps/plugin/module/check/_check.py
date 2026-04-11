from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from cleo.io.io import IO

from ps.plugin.sdk.mixins import NameAwareProtocol
from ps.plugin.sdk.project import Project


class ICheck(NameAwareProtocol, ABC):
    name: ClassVar[str]

    def can_check(self, projects: list[Project]) -> bool:
        return True

    @abstractmethod
    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]: ...

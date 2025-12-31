from abc import ABC, abstractmethod
from typing import Optional

from cleo.io.io import IO

from ps.plugin.sdk.models.project import Project


class ISolutionCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    def can_check(self, projects: list[Project]) -> bool:
        return True

    @abstractmethod
    def check(self, io: IO, projects: list[Project], fix: bool) -> Optional[Exception]: ...

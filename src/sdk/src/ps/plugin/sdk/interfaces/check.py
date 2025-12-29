from abc import ABC, abstractmethod
from typing import Optional

from cleo.io.io import IO

from ..models.project import Project


class IProjectCheck(ABC):
    @abstractmethod
    def can_check(self, project: Project) -> bool: ...

    @abstractmethod
    def check(self, io: IO, project: Project) -> Optional[Exception]: ...

    @abstractmethod
    def can_fix(self, project: Project) -> bool: ...

    @abstractmethod
    def fix(self, project: Project) -> None: ...


class ISolutionCheck(ABC):
    @abstractmethod
    def can_check(self, projects: list[Project]) -> bool: ...

    @abstractmethod
    def check(self, io: IO, projects: list[Project]) -> Optional[Exception]: ...

    @abstractmethod
    def can_fix(self, projects: list[Project]) -> bool: ...

    @abstractmethod
    def fix(self, projects: list[Project]) -> None: ...

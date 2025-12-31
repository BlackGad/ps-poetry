from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from cleo.io.io import IO

from ..models.project import Project
from ..protocols import NameAwareProtocol


class IProjectCheck(NameAwareProtocol, ABC):
    name: ClassVar[str]

    def can_check(self, project: Project) -> bool:
        return True

    @abstractmethod
    def check(self, io: IO, project: Project, fix: bool) -> Optional[Exception]: ...

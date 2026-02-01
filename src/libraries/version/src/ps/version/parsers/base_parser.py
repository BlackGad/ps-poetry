from abc import ABC, abstractmethod
from typing import Optional

from ..models import ParsedVersion


class BaseParser(ABC):
    @abstractmethod
    def parse(self, version_string: str) -> Optional[ParsedVersion]:
        pass

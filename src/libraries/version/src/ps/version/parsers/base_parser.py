from abc import ABC, abstractmethod
from typing import Optional

from ..models import Version


class BaseParser(ABC):
    @abstractmethod
    def parse(self, version_string: str) -> Optional[Version]:
        pass

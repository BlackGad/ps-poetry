from dataclasses import dataclass
from functools import total_ordering
from typing import Optional


@total_ordering
@dataclass
class VersionMetadata:
    value: str

    def __str__(self) -> str:
        return self.value

    def __call__(self, index: Optional[int] = None) -> Optional[str]:
        if self.value is None or index is None:
            return self.value
        parts = self.value.split(".")
        if index < len(parts) and index >= 0:
            return parts[index]
        return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionMetadata):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, VersionMetadata):
            return NotImplemented
        return self.value < other.value

    def __hash__(self) -> int:
        return hash(self.value)

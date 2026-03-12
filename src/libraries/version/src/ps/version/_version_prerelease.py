from dataclasses import dataclass
from functools import total_ordering
from typing import Optional


@total_ordering
@dataclass(slots=True)
class VersionPreRelease:
    name: str
    number: Optional[int] = None

    def __post_init__(self) -> None:
        if self.number is not None and self.number < 0:
            raise ValueError(f"Pre-release number must be non-negative, got {self.number}")

    def __str__(self) -> str:
        result = self.name
        if self.number is not None:
            result += str(self.number)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionPreRelease):
            return NotImplemented
        return self.name.casefold() == other.name.casefold() and (self.number or 0) == (other.number or 0)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, VersionPreRelease):
            return NotImplemented
        self_name = self.name.casefold()
        other_name = other.name.casefold()
        if self_name != other_name:
            return self_name < other_name
        return (self.number or 0) < (other.number or 0)

    def __hash__(self) -> int:
        return hash((self.name.casefold(), self.number))

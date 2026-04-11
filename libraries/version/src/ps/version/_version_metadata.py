from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass(slots=True)
class VersionMetadata:
    value: str

    def __str__(self) -> str:
        return self.value

    @property
    def parts(self) -> list[str]:
        return self.value.split(".")

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

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from typing import Optional

from .version_metadata import VersionMetadata
from .version_prerelease import VersionPreRelease
from .version_standard import VersionStandard


@total_ordering
@dataclass
class Version:
    major: int = 0
    minor: Optional[int] = None
    patch: Optional[int] = None
    rev: Optional[int] = None
    pre: Optional[VersionPreRelease] = None
    post: Optional[int] = None
    dev: Optional[int] = None
    metadata: Optional[VersionMetadata] = None
    standard: VersionStandard = VersionStandard.UNKNOWN

    def __post_init__(self) -> None:
        if self.major < 0:
            raise ValueError(f"major must be non-negative, got {self.major}")
        if self.minor is not None and self.minor < 0:
            raise ValueError(f"minor must be non-negative, got {self.minor}")
        if self.patch is not None and self.patch < 0:
            raise ValueError(f"patch must be non-negative, got {self.patch}")
        if self.rev is not None and self.rev < 0:
            raise ValueError(f"rev must be non-negative, got {self.rev}")
        if self.post is not None and self.post < 0:
            raise ValueError(f"post must be non-negative, got {self.post}")
        if self.dev is not None and self.dev < 0:
            raise ValueError(f"dev must be non-negative, got {self.dev}")

    @property
    def core(self) -> str:
        parts = [str(self.major)]
        if self.minor is not None:
            parts.append(str(self.minor))
        if self.patch is not None:
            parts.append(str(self.patch))
        if self.rev is not None and self.rev > 0:
            parts.append(str(self.rev))
        return ".".join(parts)

    def format(self, standard: VersionStandard) -> str:
        if standard == VersionStandard.PEP440:
            result = self.core
            if self.pre:
                result += str(self.pre)
            if self.post is not None:
                result += f".post{self.post}"
            if self.dev is not None:
                result += f".dev{self.dev}"
            if self.metadata:
                result += f"+{self.metadata}"
            return result

        if standard == VersionStandard.SEMVER:
            result = self.core
            if self.pre:
                result += f"-{self.pre.name}"
                if self.pre.number is not None:
                    result += f".{self.pre.number}"
            if self.metadata:
                result += f"+{self.metadata}"
            return result

        if standard == VersionStandard.NUGET:
            result = self.core
            if self.pre:
                result += f"-{self.pre.name}"
                if self.pre.number is not None:
                    result += f".{self.pre.number}"
            return result

        if standard in (VersionStandard.CALVER, VersionStandard.LOOSE):
            result = self.core
            if self.metadata:
                result += f"-{self.metadata}"
            return result

        return self.format(VersionStandard.PEP440)

    def _compare_core(self, other: Version) -> int:
        for attr in ("major", "minor", "patch", "rev"):
            self_val = getattr(self, attr) or 0
            other_val = getattr(other, attr) or 0
            if self_val < other_val:
                return -1
            if self_val > other_val:
                return 1
        return 0

    def _compare_pre(self, other: Version) -> int:
        if self.pre is None and other.pre is None:
            return 0
        if self.pre is None:
            return 1
        if other.pre is None:
            return -1

        self_name = self.pre.name.casefold()
        other_name = other.pre.name.casefold()
        if self_name < other_name:
            return -1
        if self_name > other_name:
            return 1

        self_num = self.pre.number or 0
        other_num = other.pre.number or 0
        if self_num < other_num:
            return -1
        if self_num > other_num:
            return 1
        return 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        if self._compare_core(other) != 0:
            return False

        if self._compare_pre(other) != 0:
            return False

        if (self.post or 0) != (other.post or 0):
            return False

        return (self.dev or 0) == (other.dev or 0)

    def __hash__(self) -> int:
        return hash((
            self.major,
            self.minor,
            self.patch,
            self.rev,
            self.pre.name.casefold() if self.pre else None,
            self.pre.number if self.pre else None,
            self.post,
            self.dev,
        ))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        core_cmp = self._compare_core(other)
        if core_cmp != 0:
            return core_cmp < 0

        if (self.dev or 0) != (other.dev or 0):
            if self.dev is None:
                return False
            if other.dev is None:
                return True
            return self.dev < other.dev

        pre_cmp = self._compare_pre(other)
        if pre_cmp != 0:
            return pre_cmp < 0

        self_post = self.post or 0
        other_post = other.post or 0
        if self_post != other_post:
            return self_post < other_post

        return False

    def __str__(self) -> str:
        return self.format(self.standard)

    @staticmethod
    def parse(version_string: str) -> Version:
        from ..parsers import CalVerParser, LooseParser, NuGetParser, PEP440Parser, SemVerParser

        if not version_string:
            return Version(major=0)

        version_string = version_string.strip()

        parsers = [
            PEP440Parser(),
            SemVerParser(),
            NuGetParser(),
            CalVerParser(),
            LooseParser(),
        ]

        for parser in parsers:
            result = parser.parse(version_string)
            if result:
                return result

        return Version(major=0, standard=VersionStandard.UNKNOWN)

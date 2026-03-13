# ruff: noqa: PLC0415
from dataclasses import dataclass
from functools import lru_cache, total_ordering
from typing import Optional

from ._version_metadata import VersionMetadata
from ._version_prerelease import VersionPreRelease
from ._version_constraint import VersionConstraint
from ._version_standard import VersionStandard


@lru_cache
def _get_parsers() -> list:
    from .parsers import CalVerParser, LooseParser, NuGetParser, PEP440Parser, SemVerParser

    return [
        PEP440Parser(),
        SemVerParser(),
        NuGetParser(),
        CalVerParser(),
        LooseParser(),
    ]


@total_ordering
@dataclass(slots=True)
class Version:
    major: int = 0
    minor: Optional[int] = None
    patch: Optional[int] = None
    rev: Optional[int] = None
    pre: Optional[VersionPreRelease] = None
    post: Optional[int] = None
    dev: Optional[int] = None
    metadata: Optional[VersionMetadata] = None

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

    @property
    def standards(self) -> list[VersionStandard]:
        compatible = []

        # SEMVER: requires minor and patch, no rev/post/dev
        if (
            self.minor is not None
            and self.patch is not None
            and self.rev is None
            and self.post is None
            and self.dev is None
        ):
            compatible.append(VersionStandard.SEMVER)

        # NUGET: requires minor and patch, no metadata/post/dev
        if (
            self.minor is not None
            and self.patch is not None
            and self.metadata is None
            and self.post is None
            and self.dev is None
        ):
            compatible.append(VersionStandard.NUGET)

        # CALVER: requires minor, major >= 20, no pre/post/dev
        if (
            self.minor is not None
            and self.major >= 20
            and self.pre is None
            and self.post is None
            and self.dev is None
        ):
            compatible.append(VersionStandard.CALVER)

        # LOOSE: no pre/post/dev
        if self.pre is None and self.post is None and self.dev is None:
            compatible.append(VersionStandard.LOOSE)

        # PEP440 is always compatible
        compatible.append(VersionStandard.PEP440)

        return compatible

    @property
    def format(self) -> "VersionFormatter":
        return VersionFormatter(self)

    def _compare_core(self, other: "Version") -> int:
        self_parts = (self.major, self.minor or 0, self.patch or 0, self.rev or 0)
        other_parts = (other.major, other.minor or 0, other.patch or 0, other.rev or 0)
        if self_parts < other_parts:
            return -1
        if self_parts > other_parts:
            return 1
        return 0

    def _compare_pre(self, other: "Version") -> int:
        if self.pre is None and other.pre is None:
            return 0
        if self.pre is None:
            return 1
        if other.pre is None:
            return -1

        self_parts = (self.pre.name.casefold(), self.pre.number or 0)
        other_parts = (other.pre.name.casefold(), other.pre.number or 0)
        if self_parts < other_parts:
            return -1
        if self_parts > other_parts:
            return 1
        return 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self._compare_core(other) == 0
            and self._compare_pre(other) == 0
            and (self.post or 0) == (other.post or 0)
            and (self.dev or 0) == (other.dev or 0)
        )

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

        dev_cmp = (self.dev or 0, other.dev or 0)
        if dev_cmp[0] != dev_cmp[1]:
            if self.dev is None:
                return False
            if other.dev is None:
                return True
            return self.dev < other.dev

        pre_cmp = self._compare_pre(other)
        if pre_cmp != 0:
            return pre_cmp < 0

        return (self.post or 0) < (other.post or 0)

    def __str__(self) -> str:
        standards = self.standards
        return self.format(standards[0] if standards else VersionStandard.PEP440)

    def get_constraint(self, constraint: VersionConstraint) -> str:
        major = self.major
        minor = self.minor or 0
        patch = self.patch or 0
        full_version = str(self)

        if constraint == VersionConstraint.EXACT:
            return f"=={full_version}"
        if constraint == VersionConstraint.MINIMUM_ONLY:
            return f">={full_version}"
        if constraint == VersionConstraint.RANGE_NEXT_MAJOR:
            return f">={full_version},<{major + 1}.0.0"
        if constraint == VersionConstraint.RANGE_NEXT_MINOR:
            return f">={full_version},<{major}.{minor + 1}.0"
        if constraint == VersionConstraint.RANGE_NEXT_PATCH:
            return f">={full_version},<{major}.{minor}.{patch + 1}"
        if major > 0:
            upper = f"{major + 1}.0.0"
        elif minor > 0:
            upper = f"0.{minor + 1}.0"
        else:
            upper = f"0.0.{patch + 1}"
        return f">={full_version},<{upper}"

    @staticmethod
    def parse(version_string: Optional[str]) -> Optional["Version"]:
        if version_string:
            for parser in _get_parsers():
                result = parser.parse(version_string.strip())
                if result:
                    return result
        return None


@dataclass(slots=True)
class VersionFormatter:
    version: Version

    def __call__(self, standard: VersionStandard) -> str:
        if standard == VersionStandard.PEP440:
            parts = [self.version.core]
            if self.version.pre:
                parts.append(str(self.version.pre))
            if self.version.post is not None:
                parts.append(f".post{self.version.post}")
            if self.version.dev is not None:
                parts.append(f".dev{self.version.dev}")
            if self.version.metadata:
                parts.append(f"+{self.version.metadata}")
            return "".join(parts)

        if standard == VersionStandard.SEMVER:
            parts = [self.version.core]
            if self.version.pre:
                parts.append(f"-{self.version.pre.name}")
                if self.version.pre.number is not None:
                    parts.append(f".{self.version.pre.number}")
            if self.version.metadata:
                parts.append(f"+{self.version.metadata}")
            return "".join(parts)

        if standard == VersionStandard.NUGET:
            parts = [self.version.core]
            if self.version.pre:
                parts.append(f"-{self.version.pre.name}")
                if self.version.pre.number is not None:
                    parts.append(f".{self.version.pre.number}")
            return "".join(parts)

        if standard in (VersionStandard.CALVER, VersionStandard.LOOSE):
            if self.version.metadata:
                return f"{self.version.core}-{self.version.metadata}"
            return self.version.core

        return self(VersionStandard.PEP440)

    @property
    def pep440(self) -> str:
        return self(VersionStandard.PEP440)

    @property
    def semver(self) -> str:
        return self(VersionStandard.SEMVER)

    @property
    def nuget(self) -> str:
        return self(VersionStandard.NUGET)

    @property
    def calver(self) -> str:
        return self(VersionStandard.CALVER)

    @property
    def loose(self) -> str:
        return self(VersionStandard.LOOSE)

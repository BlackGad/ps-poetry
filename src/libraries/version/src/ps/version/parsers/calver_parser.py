import re
from typing import Optional, cast

from .. import Version, VersionMetadata, VersionStandard
from .base_parser import BaseParser


class CalVerParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>20\d{2}|\d{2})"
        r"\.(?P<minor>\d+)"
        r"(?:\.(?P<patch>\d+))?"
        r"(?:\.(?P<rev>\d+))?"
        r"(?:[.\-+](?P<suffix>.+))?$"
    )

    def parse(self, version_string: str) -> Optional[Version]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        major = int(groups["major"])

        if major < 20 or (major > 99 and major < 2020):
            return None

        patch = groups["patch"]
        rev = groups["rev"]
        suffix = groups["suffix"]

        return Version(
            major=major,
            minor=int(groups["minor"]),
            patch=int(patch) if patch else None,
            rev=int(rev) if rev else None,
            metadata=VersionMetadata(cast(str, suffix)) if suffix else None,
            standard=VersionStandard.CALVER,
        )

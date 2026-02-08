import re
from typing import Optional, cast

from .. import Version, VersionMetadata, VersionStandard
from .base_parser import BaseParser


class LooseParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"(?:\.(?P<minor>\d+))?"
        r"(?:\.(?P<patch>\d+))?"
        r"(?:\.(?P<rev>\d+))?"
        r"(?:[.\-+](?P<suffix>.+))?$"
    )

    def parse(self, version_string: str) -> Optional[Version]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        minor = groups["minor"]
        patch = groups["patch"]
        rev = groups["rev"]
        suffix = groups["suffix"]

        return Version(
            major=int(groups["major"]),
            minor=int(minor) if minor else None,
            patch=int(patch) if patch else None,
            rev=int(rev) if rev else None,
            metadata=VersionMetadata(cast(str, suffix)) if suffix else None,
            standard=VersionStandard.LOOSE,
        )

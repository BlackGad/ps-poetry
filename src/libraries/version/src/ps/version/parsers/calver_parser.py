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
        major = int(groups.get("major") or 0)

        if major < 20 or (major > 99 and major < 2020):
            return None

        patch = groups.get("patch")
        rev = groups.get("rev")

        return Version(
            major=major,
            minor=int(groups.get("minor") or 0),
            patch=int(patch) if patch is not None else None,
            rev=int(rev) if rev is not None else None,
            metadata=VersionMetadata(cast(str, groups.get("suffix"))) if groups.get("suffix") else None,
            standard=VersionStandard.CALVER,
        )

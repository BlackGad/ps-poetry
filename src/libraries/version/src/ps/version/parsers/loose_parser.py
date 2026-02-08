import re
from typing import Optional, cast

from ..models import Version, VersionMetadata, VersionStandard
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
        minor = groups.get("minor")
        patch = groups.get("patch")
        rev = groups.get("rev")

        return Version(
            major=int(groups.get("major") or 0),
            minor=int(minor) if minor is not None else None,
            patch=int(patch) if patch is not None else None,
            rev=int(rev) if rev is not None else None,
            metadata=VersionMetadata(cast(str, groups.get("suffix"))) if groups.get("suffix") else None,
            standard=VersionStandard.LOOSE,
        )

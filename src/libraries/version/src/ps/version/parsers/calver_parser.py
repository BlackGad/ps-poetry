import re
from typing import Optional

from ..models import ParsedVersion, VersionStandard
from .base_parser import BaseParser


class CalVerParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>20\d{2}|\d{2})"
        r"\.(?P<minor>\d+)"
        r"(?:\.(?P<patch>\d+))?"
        r"(?:\.(?P<rev>\d+))?"
        r"(?:[.\-+](?P<suffix>.+))?$"
    )

    def parse(self, version_string: str) -> Optional[ParsedVersion]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        major = int(groups.get("major") or 0)

        if major < 20 or (major > 99 and major < 2020):
            return None

        return ParsedVersion(
            major=major,
            minor=int(groups.get("minor") or 0),
            patch=int(groups.get("patch") or 0),
            rev=int(groups.get("rev") or 0),
            meta=groups.get("suffix") or "",
            standard=VersionStandard.CALVER,
            raw=version_string,
        )

import re
from typing import Optional

from ..models import ParsedVersion, VersionStandard
from .base_parser import BaseParser


class LooseParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"(?:\.(?P<minor>\d+))?"
        r"(?:\.(?P<patch>\d+))?"
        r"(?:\.(?P<rev>\d+))?"
        r"(?:[.\-+](?P<suffix>.+))?$"
    )

    def parse(self, version_string: str) -> Optional[ParsedVersion]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        return ParsedVersion(
            major=int(groups.get("major") or 0),
            minor=int(groups.get("minor") or 0),
            patch=int(groups.get("patch") or 0),
            rev=int(groups.get("rev") or 0),
            meta=groups.get("suffix") or "",
            standard=VersionStandard.LOOSE,
            raw=version_string,
        )

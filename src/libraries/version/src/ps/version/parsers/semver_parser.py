import re
from typing import Optional

from ..models import ParsedVersion, VersionStandard
from .base_parser import BaseParser


class SemVerParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"\.(?P<minor>\d+)"
        r"\.(?P<patch>\d+)"
        r"(?:-(?P<pre>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?"
        r"(?:\+(?P<meta>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?$"
    )

    def parse(self, version_string: str) -> Optional[ParsedVersion]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        pre = groups.get("pre") or ""
        pre_label = ""
        pre_num = 0

        if pre:
            pre_parts = re.match(r"^([A-Za-z]+)\.?(\d+)?", pre)
            if pre_parts:
                pre_label = pre_parts.group(1)
                pre_num = int(pre_parts.group(2) or 0)

        return ParsedVersion(
            major=int(groups.get("major") or 0),
            minor=int(groups.get("minor") or 0),
            patch=int(groups.get("patch") or 0),
            pre_label=pre_label,
            pre_num=pre_num,
            meta=groups.get("meta") or "",
            standard=VersionStandard.SEMVER,
            raw=version_string,
        )

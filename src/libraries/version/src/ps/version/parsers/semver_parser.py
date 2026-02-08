import re
from typing import Optional

from ..models import PreRelease, Version, VersionStandard
from .base_parser import BaseParser


class SemVerParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"\.(?P<minor>\d+)"
        r"\.(?P<patch>\d+)"
        r"(?:-(?P<pre>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?"
        r"(?:\+(?P<meta>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?$"
    )

    def parse(self, version_string: str) -> Optional[Version]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        pre = groups.get("pre")
        pre_name = None
        pre_num = None

        if pre:
            pre_parts = re.match(r"^([A-Za-z]+)\.?(\d+)?", pre)
            if pre_parts:
                pre_name = pre_parts.group(1)
                if pre_parts.group(2) is not None:
                    pre_num = int(pre_parts.group(2))

            pre = PreRelease(name=pre_name, number=pre_num) if pre_name else None

        return Version(
            major=int(groups.get("major") or 0),
            minor=int(groups.get("minor") or 0),
            patch=int(groups.get("patch") or 0),
            pre=pre,
            metadata=groups.get("meta"),
            standard=VersionStandard.SEMVER,
            raw=version_string,
        )

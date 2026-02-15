import re
from typing import Optional, cast

from .. import Version, VersionPreRelease
from .base_parser import BaseParser


class NuGetParser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"\.(?P<minor>\d+)"
        r"\.(?P<patch>\d+)"
        r"(?:\.(?P<rev>\d+))?"
        r"(?:-(?P<pre>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?$"
    )

    def parse(self, version_string: str) -> Optional[Version]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        pre_str = cast(Optional[str], groups["pre"])
        pre_release: Optional[VersionPreRelease] = None

        if pre_str:
            pre_parts = re.match(r"^([A-Za-z]+)\.?(\d+)?", pre_str)
            if pre_parts:
                pre_num = pre_parts.group(2)
                pre_release = VersionPreRelease(
                    cast(str, pre_parts.group(1)),
                    int(pre_num) if pre_num else None
                )

        rev = groups["rev"]
        return Version(
            major=int(groups["major"]),
            minor=int(groups["minor"]),
            patch=int(groups["patch"]),
            rev=int(rev) if rev else None,
            pre=pre_release,
        )

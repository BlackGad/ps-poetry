import re
from typing import Optional, cast

from .. import Version, VersionMetadata, VersionPreRelease, VersionStandard
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

        meta = groups["meta"]
        return Version(
            major=int(groups["major"]),
            minor=int(groups["minor"]),
            patch=int(groups["patch"]),
            pre=pre_release,
            metadata=VersionMetadata(cast(str, meta)) if meta else None,
            standard=VersionStandard.SEMVER,
        )

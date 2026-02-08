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
        pre_str = groups.get("pre")
        pre_release: Optional[VersionPreRelease] = None

        if pre_str:
            pre_parts = re.match(r"^([A-Za-z]+)\.?(\d+)?", pre_str)
            if pre_parts:
                pre_name = pre_parts.group(1)
                pre_num = None
                if pre_parts.group(2) is not None:
                    pre_num = int(pre_parts.group(2))
                pre_release = VersionPreRelease(name=pre_name, number=pre_num)

        return Version(
            major=int(groups.get("major") or 0),
            minor=int(groups.get("minor") or 0),
            patch=int(groups.get("patch") or 0),
            pre=pre_release,
            metadata=VersionMetadata(cast(str, groups.get("meta"))) if groups.get("meta") else None,
            standard=VersionStandard.SEMVER,
        )

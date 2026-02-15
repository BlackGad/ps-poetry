import re
from typing import Optional, cast

from .. import Version, VersionMetadata, VersionPreRelease
from .base_parser import BaseParser


class PEP440Parser(BaseParser):
    PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"(?:\.(?P<minor>\d+))?"
        r"(?:\.(?P<patch>\d+))?"
        r"(?:\.(?P<rev>\d+))?"
        r"(?:(?P<pre_label>a|alpha|b|beta|rc|c|pre|preview)(?P<pre_num>\d+))?"
        r"(?:\.post(?P<post>\d+))?"
        r"(?:\.dev(?P<dev>\d+))?"
        r"(?:\+(?P<meta>.+))?$",
        re.IGNORECASE,
    )

    def parse(self, version_string: str) -> Optional[Version]:
        match = self.PATTERN.match(version_string)
        if not match:
            return None

        groups = match.groupdict()
        minor = groups["minor"]
        patch = groups["patch"]
        rev = groups["rev"]
        pre_label = groups["pre_label"]
        pre_num = groups["pre_num"]
        post = groups["post"]
        dev = groups["dev"]
        meta = groups["meta"]

        return Version(
            major=int(groups["major"]),
            minor=int(minor) if minor else None,
            patch=int(patch) if patch else None,
            rev=int(rev) if rev else None,
            pre=VersionPreRelease(pre_label, int(pre_num)) if pre_label and pre_num else None,
            post=int(post) if post else None,
            dev=int(dev) if dev else None,
            metadata=VersionMetadata(cast(str, meta)) if meta else None,
        )

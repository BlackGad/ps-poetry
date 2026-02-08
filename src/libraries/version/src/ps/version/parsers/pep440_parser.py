import re
from typing import Optional, cast

from ..models import Version, VersionMetadata, VersionPreRelease, VersionStandard
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
        minor = groups.get("minor")
        patch = groups.get("patch")
        rev = groups.get("rev")
        pre_num = groups.get("pre_num")
        pre_label = groups.get("pre_label")
        post = groups.get("post")
        dev = groups.get("dev")

        pre = (
            VersionPreRelease(name=pre_label, number=int(pre_num))
            if pre_label and pre_num is not None
            else None
        )

        return Version(
            major=int(groups.get("major") or 0),
            minor=int(minor) if minor is not None else None,
            patch=int(patch) if patch is not None else None,
            rev=int(rev) if rev is not None else None,
            pre=pre,
            post=int(post) if post is not None else None,
            dev=int(dev) if dev is not None else None,
            metadata=VersionMetadata(cast(str, groups.get("meta"))) if groups.get("meta") else None,
            standard=VersionStandard.PEP440,
        )

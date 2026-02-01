import re
from typing import Optional

from ..models import ParsedVersion, VersionStandard
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
            pre_label=groups.get("pre_label") or "",
            pre_num=int(groups.get("pre_num") or 0),
            post=int(groups.get("post") or 0),
            dev=int(groups.get("dev") or 0),
            meta=groups.get("meta") or "",
            standard=VersionStandard.PEP440,
            raw=version_string,
        )

from dataclasses import dataclass
from typing import Optional

from .version_standard import VersionStandard


@dataclass
class PreRelease:
    name: str
    number: Optional[int] = None


@dataclass
class Version:
    major: int
    minor: Optional[int] = None
    patch: Optional[int] = None
    rev: Optional[int] = None
    pre: Optional[PreRelease] = None
    post: Optional[int] = None
    dev: Optional[int] = None
    metadata: Optional[str] = None
    standard: VersionStandard = VersionStandard.UNKNOWN
    raw: Optional[str] = None

    @property
    def core(self) -> str:
        parts = [str(self.major)]
        if self.minor is not None:
            parts.append(str(self.minor))
        if self.patch is not None:
            parts.append(str(self.patch))
        if self.rev is not None and self.rev > 0:
            parts.append(str(self.rev))
        return ".".join(parts)

    @property
    def pre_text(self) -> str:
        if not self.pre:
            return ""

        result = self.pre.name
        if self.pre.number is not None and self.pre.number > 0:
            result += str(self.pre.number)
        return result

    def meta(self, index: int) -> Optional[str]:
        if not self.metadata:
            return None

        if index < 0:
            return None

        parts = self.metadata.split(".", 1)
        if index == 0:
            return parts[0]

        if index == 1 and len(parts) > 1:
            return parts[1]

        return None

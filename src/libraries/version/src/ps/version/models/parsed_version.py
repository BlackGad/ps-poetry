from dataclasses import dataclass

from .version_standard import VersionStandard


@dataclass
class ParsedVersion:
    major: int = 0
    minor: int = 0
    patch: int = 0
    rev: int = 0
    pre_label: str = ""
    pre_num: int = 0
    post: int = 0
    dev: int = 0
    meta: str = ""
    standard: VersionStandard = VersionStandard.UNKNOWN
    raw: str = ""

    @property
    def core(self) -> str:
        parts = [str(self.major), str(self.minor), str(self.patch)]
        if self.rev > 0:
            parts.append(str(self.rev))
        return ".".join(parts)

    @property
    def pre(self) -> str:
        if self.pre_label:
            result = self.pre_label
            if self.pre_num > 0:
                result += str(self.pre_num)
            return result
        return ""

    @property
    def meta0(self) -> str:
        if self.meta:
            parts = self.meta.split(".", 1)
            return parts[0]
        return ""

    @property
    def meta1(self) -> str:
        if self.meta:
            parts = self.meta.split(".", 1)
            if len(parts) > 1:
                return parts[1]
        return ""

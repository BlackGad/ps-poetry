from enum import Enum


class VersionStandard(Enum):
    PEP440 = "pep440"
    SEMVER = "semver"
    NUGET = "nuget"
    CALVER = "calver"
    LOOSE = "loose"

from .models import ParsedVersion, VersionStandard
from .parsers import (
    CalVerParser,
    LooseParser,
    NuGetParser,
    PEP440Parser,
    SemVerParser,
)


class VersionParser:
    _parsers = [
        PEP440Parser(),
        SemVerParser(),
        NuGetParser(),
        CalVerParser(),
        LooseParser(),
    ]

    @staticmethod
    def parse(version_string: str) -> ParsedVersion:
        if not version_string:
            return ParsedVersion(raw=version_string)

        version_string = version_string.strip()

        for parser in VersionParser._parsers:
            result = parser.parse(version_string)
            if result:
                return result

        return ParsedVersion(raw=version_string, standard=VersionStandard.UNKNOWN)

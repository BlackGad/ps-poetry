import re
from typing import Callable, Iterable, Optional, Sequence, Tuple, Union

from .models import Version, VersionStandard
from .parsers import (
    CalVerParser,
    LooseParser,
    NuGetParser,
    PEP440Parser,
    SemVerParser,
)


TokenValue = Union[str, int, bool]
TokenResolver = Callable[[list[str]], Optional[TokenValue]]
TokenResolverEntry = Tuple[str, TokenResolver]

_TOKEN_PATTERN = re.compile(r"\{([^{}]+)\}")
_PARSERS = [
    PEP440Parser(),
    SemVerParser(),
    NuGetParser(),
    CalVerParser(),
    LooseParser(),
]


class VersionParser:
    def __init__(self, token_resolvers: Sequence[TokenResolverEntry]) -> None:
        self._token_resolvers = list(token_resolvers)

    @staticmethod
    def parse(version_string: str) -> Version:
        if not version_string:
            return Version(major=0, raw=version_string)

        version_string = version_string.strip()

        for parser in _PARSERS:
            result = parser.parse(version_string)
            if result:
                return result

        return Version(major=0, raw=version_string, standard=VersionStandard.UNKNOWN)

    def parse_inputs(self, inputs: Iterable[str]) -> Version:
        for input_value in inputs:
            if input_value is None:
                continue

            condition, version_string, valid = self._split_condition(input_value)
            if not valid:
                continue

            if condition is not None and not self._condition_matches(
                self.materialize(condition)
            ):
                continue

            result = VersionParser.parse(self.materialize(version_string))
            if result.standard != VersionStandard.UNKNOWN:
                return result

        return Version(major=0)

    @staticmethod
    def _split_condition(value: str) -> Tuple[Optional[str], str, bool]:
        if value is None:
            return None, "", False

        text = value.strip()
        if not text.startswith("["):
            return None, text, True

        end_index = text.find("]")
        if end_index == -1:
            return None, text, False

        condition = text[1:end_index].strip()
        remainder = text[end_index + 1:].strip()
        if not condition:
            return None, remainder or text, False

        return condition, remainder, True

    def materialize(self, value: str) -> str:
        if not value:
            return value

        def resolve(match: re.Match[str]) -> str:
            expression = match.group(1)
            parts = expression.split(":")
            key = parts[0]
            if not key:
                return match.group(0)

            args = parts[1:]

            for resolver_key, resolver in self._token_resolvers:
                if resolver_key != key:
                    continue
                resolved = resolver(args)
                if resolved is not None:
                    return str(resolved)

            return match.group(0)

        return _TOKEN_PATTERN.sub(resolve, value)

    def _condition_matches(self, _condition: str) -> bool:
        # TODO: implement condition execution.
        return True

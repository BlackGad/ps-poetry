from typing import Optional

from ps.token_expressions.token_resolvers import BaseResolver
from ps.token_expressions.token_resolvers._base_resolver import TokenValue
from ps.version import Version


class VersionResolver(BaseResolver):
    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return None

        version = Version.parse(args[0])
        if version is None:
            return None

        if len(args) == 1:
            return str(version)

        sub_resolver = BaseResolver.pick_resolver(version)
        return sub_resolver(args[1:])

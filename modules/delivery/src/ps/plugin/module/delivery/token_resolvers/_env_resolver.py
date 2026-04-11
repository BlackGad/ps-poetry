import os
from typing import Optional

from ps.token_expressions import BaseResolver
from ps.token_expressions.token_resolvers._base_resolver import TokenValue


class EnvResolver(BaseResolver):
    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return None
        return os.getenv(args[0])

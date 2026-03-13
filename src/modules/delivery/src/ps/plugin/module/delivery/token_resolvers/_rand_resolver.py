import random
import uuid
from typing import Optional

from ps.token_expressions import BaseResolver
from ps.token_expressions.token_resolvers._base_resolver import TokenValue

_DEFAULT_HASH_LENGTH: int = 8


class RandResolver(BaseResolver):
    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return None

        kind = args[0]

        if kind == "uuid":
            return str(uuid.uuid4())

        if kind == "hash":
            return uuid.uuid4().hex[:_DEFAULT_HASH_LENGTH]

        if kind == "num":
            if len(args) >= 2:
                return _parse_range(args[1])
            return random.randint(0, 2**31 - 1)

        return None


def _parse_range(range_str: str) -> Optional[int]:
    if ".." not in range_str:
        return None
    parts = range_str.split("..", 1)
    try:
        low = int(parts[0])
        high = int(parts[1])
    except ValueError:
        return None
    if low > high:
        return None
    return random.randint(low, high)

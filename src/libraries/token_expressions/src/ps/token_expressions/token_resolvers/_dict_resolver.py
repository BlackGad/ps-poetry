from typing import Any, Optional

from ._base_resolver import BaseResolver, TokenResolver, TokenValue


class DictResolver(BaseResolver):
    @staticmethod
    def resolve_factory(source: Any) -> Optional[TokenResolver]:
        if isinstance(source, dict):
            return DictResolver(source)
        return None

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return None

        current: Any = self._data
        args_len = len(args)

        for i, arg in enumerate(args):
            next_value = current.get(arg) if isinstance(current, dict) else getattr(current, arg, None)

            if next_value is None:
                return None

            if isinstance(next_value, (str, int, bool)):
                return next_value if i == args_len - 1 else None

            if i < args_len - 1:
                next_resolver = BaseResolver.pick_resolver(next_value)
                if next_resolver:
                    return next_resolver(args[i + 1:])

            if i == args_len - 1:
                return next_value if isinstance(next_value, (str, int, bool)) else None

            current = next_value

        return None

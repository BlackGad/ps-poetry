from typing import Callable, Optional

from .base_resolver import BaseResolver, TokenValue


class FuncResolver(BaseResolver):
    def __init__(self, func: Callable[[str], Optional[TokenValue]]):
        self._func = func

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        try:
            result = self._func(args[0] if args else "")
        except Exception:
            return None

        if result is None:
            return None

        if not isinstance(result, (str, int, bool, list)):
            if len(args) > 1:
                sub_resolver = self.pick_resolver(result)
                if sub_resolver is None:
                    return None
                return sub_resolver(args[1:])
            return str(result)

        return result

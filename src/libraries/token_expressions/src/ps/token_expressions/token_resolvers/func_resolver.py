from typing import Callable, Optional

from .base_resolver import BaseResolver, TokenValue


class FuncResolver(BaseResolver):
    def __init__(self, func: Callable[[list[str]], Optional[TokenValue]]):
        super().__init__(None)
        self._func = func

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        try:
            return self._func(args)
        except Exception:
            return None

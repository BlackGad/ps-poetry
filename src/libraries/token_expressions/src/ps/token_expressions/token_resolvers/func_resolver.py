from typing import Callable, Optional, Union


TokenValue = Union[str, int, bool]


class FuncResolver:
    def __init__(self, func: Callable[[list[str]], Optional[TokenValue]]):
        self._func = func

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        try:
            return self._func(args)
        except Exception:
            return None

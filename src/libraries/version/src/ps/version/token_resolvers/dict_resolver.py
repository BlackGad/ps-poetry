from typing import Any, Callable, Optional, Union

TokenValue = Union[str, int, bool]
TokenResolverFunc = Callable[[list[str]], Optional[TokenValue]]
PickerFunc = Callable[[Any], TokenResolverFunc]


class DictResolver:
    def __init__(self, data: dict[str, Any], picker: Optional[PickerFunc] = None):
        self._data = data
        self._picker = picker

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return None

        current: Any = self._data
        for i, arg in enumerate(args):
            next_value = current.get(arg) if isinstance(current, dict) else getattr(current, arg, None)

            if next_value is None:
                return None

            if isinstance(next_value, (str, int, bool)):
                if i == len(args) - 1:
                    return next_value
                return None
            if self._picker:
                remaining_args = args[i + 1:]
                if remaining_args:
                    next_resolver = self._picker(next_value)
                    return next_resolver(remaining_args)
                if isinstance(next_value, (str, int, bool)):
                    return next_value
                return None
            current = next_value

        return None

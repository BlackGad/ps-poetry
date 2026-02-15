from typing import Any, Optional

from .base_resolver import BaseResolver, PickerFunc, TokenValue


class ListResolver(BaseResolver):
    def __init__(self, data: list[Any], picker: PickerFunc):
        super().__init__(picker)
        self._data = data

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            if all(isinstance(item, (str, int, bool)) for item in self._data):
                return self._data
            return str(self._data)

        current: Any = self._data
        args_len = len(args)

        for i, arg in enumerate(args):
            if not isinstance(current, list):
                return None

            try:
                index = int(arg)
            except (ValueError, TypeError):
                return None

            if index < 0 or index >= len(current):
                return None

            next_value = current[index]

            if next_value is None:
                return None

            if isinstance(next_value, (str, int, bool)):
                return next_value if i == args_len - 1 else None

            if i < args_len - 1:
                next_resolver = self.pick_resolver(next_value)
                if next_resolver:
                    return next_resolver(args[i + 1:])

            if i == args_len - 1:
                return next_value if isinstance(next_value, (str, int, bool)) else None

            current = next_value

        return None

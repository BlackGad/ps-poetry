from typing import Callable, Optional, cast

from .base_resolver import BaseResolver, PickerFunc, TokenValue


class InstanceResolver(BaseResolver):
    def __init__(self, instance: object, picker: PickerFunc):
        super().__init__(picker)
        self._instance = instance

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return str(self._instance)

        resolved = self._resolve_nested_attributes(args)

        if resolved is not None:
            resolved = self._confirm_resolution(args, resolved)

        if resolved is None and callable(self._instance):
            resolved = self._try_callable_fallback(args)

        return cast(Optional[TokenValue], resolved)

    def _resolve_nested_attributes(self, args: list[str]) -> Optional[TokenValue]:
        current = self._instance
        args_len = len(args)

        for i, arg in enumerate(args):
            next_value = getattr(current, arg, None)
            if next_value is None:
                return None

            if isinstance(next_value, (str, int, bool)):
                if i == args_len - 1:
                    return next_value
                return None

            if i < args_len - 1:
                next_resolver = self.pick_resolver(next_value)
                if next_resolver:
                    result = next_resolver(args[i + 1:])
                    return result if result is not None else None
            else:
                current = next_value

        return cast(Optional[TokenValue], current) if current is not self._instance else None

    def _confirm_resolution(self, args: list[str], resolved: TokenValue) -> Optional[TokenValue]:
        confirm_method = getattr(self._instance, "confirm_resolve", None)
        if confirm_method is None or not callable(confirm_method):
            return resolved

        confirm_method = cast(Callable[[list[str], str], bool], confirm_method)
        try:
            if not confirm_method(args, str(resolved)):
                return None
        except Exception:
            return None

        return resolved

    def _try_callable_fallback(self, args: list[str]) -> Optional[TokenValue]:
        try:
            result = cast(Callable[[list[str]], Optional[TokenValue]], self._instance)(args)
            return result
        except Exception:
            return None

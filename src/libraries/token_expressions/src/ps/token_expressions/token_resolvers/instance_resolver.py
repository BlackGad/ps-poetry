from typing import Any, Callable, Optional, Union, cast

TokenValue = Union[str, int, bool]
TokenResolverFunc = Callable[[list[str]], Optional[TokenValue]]
PickerFunc = Callable[[Any], TokenResolverFunc]


class InstanceResolver:
    def __init__(self, instance: object, picker: Optional[PickerFunc] = None):
        self._instance = instance
        self._picker = picker

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        resolved = None

        if args:
            current = self._instance
            resolved_all = True
            args_len = len(args)

            for i, arg in enumerate(args):
                next_value = getattr(current, arg, None)
                if next_value is None:
                    resolved_all = False
                    break

                if isinstance(next_value, (str, int, bool)):
                    if i == args_len - 1:
                        current = next_value
                    else:
                        resolved_all = False
                        break
                elif self._picker and i < args_len - 1:
                    next_resolver = self._picker(next_value)
                    result = next_resolver(args[i + 1:])
                    if result is None:
                        resolved_all = False
                    current = result
                    break
                else:
                    current = next_value

            resolved = current if resolved_all and current is not self._instance else None

            if resolved is not None:
                confirm_method = getattr(self._instance, "confirm_resolve", None)
                if confirm_method is not None and callable(confirm_method):
                    confirm_method = cast(
                        Callable[[list[str], str], bool],
                        confirm_method,
                    )
                    try:
                        if not confirm_method(args, str(resolved)):
                            resolved = None
                    except Exception:
                        resolved = None

        if resolved is None and callable(self._instance):
            try:
                resolved = self._instance(args)
            except Exception:
                resolved = None

        return cast(Optional[TokenValue], resolved)

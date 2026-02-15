from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Union

TokenValue = Union[str, int, bool, list[Union[str, int, bool]]]
TokenResolverFunc = Callable[[list[str]], Optional[TokenValue]]
TokenResolver = TokenResolverFunc
PickerFunc = Callable[[Any], TokenResolverFunc]


class BaseResolver(ABC):
    def __init__(self, picker: Optional[PickerFunc]):
        self._picker = picker

    @abstractmethod
    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        pass

    def pick_resolver(self, value: Any) -> Optional[TokenResolverFunc]:
        if self._picker:
            return self._picker(value)
        return None

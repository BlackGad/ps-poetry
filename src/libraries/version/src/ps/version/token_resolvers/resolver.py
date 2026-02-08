import inspect
from typing import Any, Callable, Optional, Union

from .dict_resolver import DictResolver
from .func_resolver import FuncResolver
from .instance_resolver import InstanceResolver


TokenValue = Union[str, int, bool]
TokenResolver = Callable[[list[str]], Optional[TokenValue]]


def pick_resolver(source: Any) -> TokenResolver:
    if isinstance(source, dict):
        return DictResolver(source, pick_resolver)
    if inspect.isfunction(source) or inspect.ismethod(source):
        return FuncResolver(source)
    return InstanceResolver(source, pick_resolver)

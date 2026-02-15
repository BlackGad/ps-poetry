import inspect
from typing import Any

from .base_resolver import TokenResolver
from .dict_resolver import DictResolver
from .func_resolver import FuncResolver
from .instance_resolver import InstanceResolver
from .list_resolver import ListResolver
from .none_resolver import NoneResolver


def _pick_resolver(source: Any) -> TokenResolver:
    if source is None:
        return NoneResolver()
    if isinstance(source, dict):
        return DictResolver(source, _pick_resolver)
    if isinstance(source, list):
        return ListResolver(source, _pick_resolver)
    if inspect.isfunction(source) or inspect.ismethod(source):
        return FuncResolver(source)
    return InstanceResolver(source, _pick_resolver)

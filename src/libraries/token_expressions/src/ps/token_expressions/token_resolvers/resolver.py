import inspect
from typing import Any

from .base_resolver import BaseResolver, TokenResolver
from .dict_resolver import DictResolver
from .func_resolver import FuncResolver
from .instance_resolver import InstanceResolver
from .list_resolver import ListResolver
from .none_resolver import NoneResolver


def _pick_resolver(source: Any) -> TokenResolver:
    if source is None:
        resolver: BaseResolver = NoneResolver()
    elif isinstance(source, BaseResolver):
        resolver = source
    elif isinstance(source, dict):
        resolver = DictResolver(source)
    elif isinstance(source, list):
        resolver = ListResolver(source)
    elif inspect.isfunction(source) or inspect.ismethod(source):
        resolver = FuncResolver(source)
    else:
        resolver = InstanceResolver(source)
    resolver._bind_picker(_pick_resolver)
    return resolver

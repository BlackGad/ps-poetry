from ._base_resolver import BaseResolver, ResolverFactory
from ._dict_resolver import DictResolver
from ._func_resolver import FuncResolver
from ._instance_resolver import InstanceResolver
from ._list_resolver import ListResolver
from ._none_resolver import NoneResolver

BaseResolver.register_resolvers([
    NoneResolver.resolve_factory,
    BaseResolver.resolve_factory,
    DictResolver.resolve_factory,
    ListResolver.resolve_factory,
    FuncResolver.resolve_factory,
    InstanceResolver.resolve_factory,
])

__all__ = [
    "BaseResolver",
    "ResolverFactory",
]

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Iterable, Optional, Union

TokenValue = Union[str, int, bool, list[Union[str, int, bool]]]
TokenResolverFunc = Callable[[list[str]], Optional[TokenValue]]
TokenResolver = TokenResolverFunc
ResolverFactory = Callable[[Any], Optional[TokenResolver]]


class BaseResolver(ABC):
    _FACTORIES: ClassVar[list[ResolverFactory]] = []

    @staticmethod
    def resolve_factory(source: Any) -> Optional[TokenResolver]:
        if isinstance(source, BaseResolver):
            return source
        return None

    @classmethod
    def register_resolvers(cls, factories: Iterable[ResolverFactory]) -> None:
        for factory in factories:
            cls._FACTORIES.append(factory)

    @classmethod
    def pick_resolver(cls, source: Any) -> TokenResolver:
        for factory in cls._FACTORIES:
            resolver = factory(source)
            if resolver is not None:
                return resolver
        raise ValueError(f"No resolver registered for type: {type(source)}")

    @abstractmethod
    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        pass

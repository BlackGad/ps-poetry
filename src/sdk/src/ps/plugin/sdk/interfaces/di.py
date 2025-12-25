from abc import ABC, abstractmethod
from typing import Callable, List, Optional, ParamSpec, Type, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class DI(ABC):
    @abstractmethod
    def singleton(self, cls: Type[T]) -> "Binding[T]": ...

    @abstractmethod
    def transient(self, cls: Type[T]) -> "Binding[T]": ...

    @abstractmethod
    def resolve(self, key: Type[T]) -> Optional[T]: ...

    @abstractmethod
    def resolve_many(self, key: Type[T]) -> List[T]: ...


class Binding[T](ABC):
    @abstractmethod
    def implementation(self, impl: Type[T]) -> None: ...

    @abstractmethod
    def factory(self, factory: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None: ...

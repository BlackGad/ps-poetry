from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Callable, List, Optional, ParamSpec, Type, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class Lifetime(IntEnum):
    UNKNOWN = 0
    SINGLETON = 1
    TRANSIENT = 2


class Priority(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2


class DI(ABC):
    @abstractmethod
    def register(self, cls: Type[T] | str, lifetime: Lifetime = Lifetime.SINGLETON, priority: Priority = Priority.LOW) -> "Binding[T]": ...

    @abstractmethod
    def resolve(self, key: Type[T]) -> Optional[T]: ...

    @abstractmethod
    def resolve_many(self, key: Type[T]) -> List[T]: ...

    @abstractmethod
    def spawn(self, cls: Type[T], *args: Any, **kwargs: Any) -> T: ...


class Binding[T](ABC):
    @abstractmethod
    def implementation(self, impl: Type[T]) -> None: ...

    @abstractmethod
    def factory(self, factory: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None: ...

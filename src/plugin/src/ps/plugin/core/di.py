import threading
from enum import IntEnum
from typing import Callable, List, Optional, ParamSpec, Type, TypeVar, cast

from ps.plugin.sdk import DI, Binding

T = TypeVar("T")
P = ParamSpec("P")


class _Lifetime(IntEnum):
    UNKNOWN = 0
    SINGLETON = 1
    TRANSIENT = 2


class _Registration[T]:
    def __init__(self, lifetime: _Lifetime, factory: Callable[[], T]) -> None:
        self.lifetime = lifetime
        self.factory = factory
        self.instance: Optional[T] = None
        self._lock_singleton_creation = threading.Lock()

    def resolve(self) -> T:
        match self.lifetime:
            case _Lifetime.SINGLETON:
                if self.instance is None:
                    with self._lock_singleton_creation:
                        if self.instance is None:
                            self.instance = self.factory()
                return self.instance
            case _Lifetime.TRANSIENT:
                return self.factory()
            case _:
                raise ValueError("Unknown lifetime for registration.")


class _Registrations:
    def __init__(self) -> None:
        self._registrations: List[_Registration] = []
        self._lock_registrations_access = threading.Lock()

    def add_registration(self, registration: _Registration) -> None:
        with self._lock_registrations_access:
            self._registrations.insert(0, registration)

    def resolve_first(self) -> object:
        with self._lock_registrations_access:
            registration = self._registrations[0]
        return registration.resolve()

    def resolve_all(self) -> List:
        with self._lock_registrations_access:
            registrations = list(self._registrations)
        return [registration.resolve() for registration in registrations]


class _DI(DI):
    def __init__(self) -> None:
        self._registry: dict[Type, _Registrations] = {}
        self._lock_registry_access = threading.Lock()

    def singleton(self, cls: Type[T]) -> "Binding[T]":
        return _Binding(self, cls, lifetime=_Lifetime.SINGLETON)

    def transient(self, cls: Type[T]) -> "Binding[T]":
        return _Binding(self, cls, lifetime=_Lifetime.TRANSIENT)

    def resolve(self, key: Type[T]) -> Optional[T]:
        with self._lock_registry_access:
            registrations = self._registry.get(key)
        if registrations is None:
            return None
        return cast(T, registrations.resolve_first())

    def resolve_many(self, key: Type[T]) -> List[T]:
        with self._lock_registry_access:
            registrations = self._registry.get(key)
        if registrations is None:
            return []
        return registrations.resolve_all()

    def _register(self, cls: Type[T], registration: _Registration[T]) -> None:
        with self._lock_registry_access:
            registrations = self._registry.setdefault(cls, _Registrations())
        registrations.add_registration(registration)


class _Binding[T](Binding[T]):
    def __init__(self, di: _DI, cls: Type[T], lifetime: _Lifetime) -> None:
        self._di = di
        self._cls = cls
        self._lifetime = lifetime

    def implementation(self, impl: Type[T]) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, lambda: impl()))

    def factory(self, factory: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, lambda: factory(*args, **kwargs)))

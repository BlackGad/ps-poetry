import threading
from typing import Callable, List, Optional

from ._enums import Lifetime, Priority


class _Registration[T]:
    def __init__(self, lifetime: Lifetime, priority: Priority, factory: Callable[[], T]) -> None:
        self.lifetime = lifetime
        self.priority = priority
        self.factory = factory
        self.instance: Optional[T] = None
        self._lock_singleton_creation = threading.Lock()

    def resolve(self) -> T:
        match self.lifetime:
            case Lifetime.SINGLETON:
                if self.instance is None:
                    with self._lock_singleton_creation:
                        if self.instance is None:
                            self.instance = self.factory()
                return self.instance
            case Lifetime.TRANSIENT:
                return self.factory()
            case _:
                raise ValueError("Unknown lifetime for registration.")


class _Registrations:
    def __init__(self) -> None:
        self._registrations: List[_Registration] = []
        self._lock_registrations_access = threading.Lock()

    def add_registration(self, registration: _Registration) -> None:
        with self._lock_registrations_access:
            insert_pos = 0
            for i, existing in enumerate(self._registrations):
                if registration.priority >= existing.priority:
                    insert_pos = i
                    break
                insert_pos = i + 1
            self._registrations.insert(insert_pos, registration)

    def resolve_first(self) -> object:
        with self._lock_registrations_access:
            registration = self._registrations[0]
        return registration.resolve()

    def resolve_all(self) -> List:
        with self._lock_registrations_access:
            registrations = list(self._registrations)
        return [registration.resolve() for registration in registrations]

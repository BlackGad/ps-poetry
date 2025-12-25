import inspect
import threading
from enum import IntEnum
from typing import Any, Callable, List, Optional, ParamSpec, Type, TypeVar, Union, cast, get_args, get_origin, get_type_hints

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
        self._signature_cache: dict[Type, inspect.Signature] = {}
        self._type_name_cache: dict[str, Type] = {}

    def _resolve_type(self, key: Type[T] | str) -> Type[T]:
        """Resolve a type from either a Type object or a string name."""
        if isinstance(key, str):
            if key not in self._type_name_cache:
                # Try to find the type in the registry by matching __name__
                for registered_type in self._registry:
                    if registered_type.__name__ == key:
                        self._type_name_cache[key] = registered_type
                        return registered_type
                raise ValueError(f"Cannot resolve type from string '{key}' - no matching type registered")
            return self._type_name_cache[key]
        return key

    def singleton(self, cls: Type[T] | str) -> "Binding[T]":
        resolved_cls = self._resolve_type(cls) if isinstance(cls, str) else cls
        return _Binding(self, resolved_cls, lifetime=_Lifetime.SINGLETON)

    def transient(self, cls: Type[T] | str) -> "Binding[T]":
        resolved_cls = self._resolve_type(cls) if isinstance(cls, str) else cls
        return _Binding(self, resolved_cls, lifetime=_Lifetime.TRANSIENT)

    def resolve(self, key: Type[T] | str) -> Optional[T]:
        resolved_key = self._resolve_type(key) if isinstance(key, str) else key
        with self._lock_registry_access:
            registrations = self._registry.get(resolved_key)
        if registrations is None:
            return None
        return cast(T, registrations.resolve_first())

    def resolve_many(self, key: Type[T] | str) -> List[T]:
        resolved_key = self._resolve_type(key) if isinstance(key, str) else key
        with self._lock_registry_access:
            registrations = self._registry.get(resolved_key)
        if registrations is None:
            return []
        return registrations.resolve_all()

    def _register(self, cls: Type[T], registration: _Registration[T]) -> None:
        with self._lock_registry_access:
            registrations = self._registry.setdefault(cls, _Registrations())
        registrations.add_registration(registration)

    def spawn(self, cls: Type[T], *args: Any, **kwargs: Any) -> T:  # noqa: C901
        # Get or cache signature
        if cls not in self._signature_cache:
            self._signature_cache[cls] = inspect.signature(cls.__init__)
        sig = self._signature_cache[cls]

        # Get type hints (handles string annotations from __future__)
        try:
            type_hints = get_type_hints(cls.__init__)
        except Exception:
            type_hints = {}

        final_kwargs = dict(kwargs)
        params_list = list(sig.parameters.values())[1:]  # Skip 'self'

        # Process positional args
        for i, arg in enumerate(args):
            if i < len(params_list):
                final_kwargs[params_list[i].name] = arg

        # Resolve missing parameters
        for param in params_list:
            if param.name in final_kwargs:
                continue

            # Get resolved type hint or fall back to annotation
            annotation = type_hints.get(param.name, param.annotation)
            if annotation == inspect.Parameter.empty:
                continue

            has_default = param.default != inspect.Parameter.empty

            # Special case: DI itself
            if annotation is DI or (isinstance(annotation, type) and issubclass(annotation, DI)):
                final_kwargs[param.name] = self
                continue

            # Check if it's List[T]
            origin = get_origin(annotation)
            if origin is list:
                type_args = get_args(annotation)
                if type_args:
                    final_kwargs[param.name] = self.resolve_many(type_args[0])
                continue

            # Check if it's Optional[T] (Union[T, None])
            if origin is Union:
                type_args = get_args(annotation)
                if type(None) in type_args:
                    non_none_type = next(t for t in type_args if t is not type(None))
                    resolved = self.resolve(non_none_type)
                    if resolved is not None:
                        final_kwargs[param.name] = resolved
                    elif has_default:
                        final_kwargs[param.name] = param.default
                    continue

            # Simple Type - required resolve
            resolved = self.resolve(annotation)
            if resolved is not None:
                final_kwargs[param.name] = resolved
            elif has_default:
                final_kwargs[param.name] = param.default
            else:
                raise ValueError(f"Cannot resolve required dependency {annotation} for parameter {param.name}")

        return cls(**final_kwargs)


class _Binding[T](Binding[T]):
    def __init__(self, di: _DI, cls: Type[T], lifetime: _Lifetime) -> None:
        self._di = di
        self._cls = cls
        self._lifetime = lifetime

    def implementation(self, impl: Type[T]) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, lambda: impl()))

    def factory(self, factory: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, lambda: factory(*args, **kwargs)))

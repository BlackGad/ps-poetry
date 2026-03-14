import inspect
import threading
from typing import Any, Callable, List, Optional, ParamSpec, Type, TypeVar, Union, cast, get_args, get_origin, get_type_hints

from ._enums import Lifetime, Priority
from ._registration import _Registration, _Registrations

T = TypeVar("T")
P = ParamSpec("P")


class Binding[T]:
    def __init__(self, di: "DI", cls: Type[T], lifetime: Lifetime, priority: Priority) -> None:
        self._di = di
        self._cls = cls
        self._lifetime = lifetime
        self._priority = priority

    def implementation(self, impl: Type[T]) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, self._priority, lambda: self._di.spawn(impl)))

    def factory(self, factory: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, self._priority, lambda: factory(*args, **kwargs)))


class DI:
    def __init__(self) -> None:
        self._registry: dict[Type, _Registrations] = {}
        self._lock_registry_access = threading.Lock()
        self._signature_cache: dict[Type, inspect.Signature] = {}
        self._type_name_cache: dict[str, Type] = {}

    def _resolve_type(self, key: Type[T] | str) -> Type[T]:
        if isinstance(key, str):
            if key not in self._type_name_cache:
                for registered_type in self._registry:
                    if registered_type.__name__ == key:
                        self._type_name_cache[key] = registered_type
                        return registered_type
                raise ValueError(f"Cannot resolve type from string '{key}' - no matching type registered")
            return self._type_name_cache[key]
        return key

    def register(self, cls: Type[T] | str, lifetime: Lifetime = Lifetime.SINGLETON, priority: Priority = Priority.LOW) -> Binding[T]:
        resolved_cls = cast(Type[T], self._resolve_type(cls)) if isinstance(cls, str) else cls
        return Binding(self, resolved_cls, lifetime=lifetime, priority=priority)

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
        if cls not in self._signature_cache:
            self._signature_cache[cls] = inspect.signature(cls.__init__)
        sig = self._signature_cache[cls]

        try:
            type_hints = get_type_hints(cls.__init__)
        except Exception:
            type_hints = {}

        final_kwargs = dict(kwargs)
        params_list = list(sig.parameters.values())[1:]  # Skip 'self'

        for i, arg in enumerate(args):
            if i < len(params_list):
                final_kwargs[params_list[i].name] = arg

        for param in params_list:
            if param.name in final_kwargs:
                continue

            annotation = type_hints.get(param.name, param.annotation)
            if annotation == inspect.Parameter.empty:
                continue

            has_default = param.default != inspect.Parameter.empty

            if annotation is DI or (isinstance(annotation, type) and issubclass(annotation, DI)):
                final_kwargs[param.name] = self
                continue

            origin = get_origin(annotation)
            if origin is list:
                type_args = get_args(annotation)
                if type_args:
                    final_kwargs[param.name] = self.resolve_many(type_args[0])
                continue

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

            resolved = self.resolve(annotation)
            if resolved is not None:
                final_kwargs[param.name] = resolved
            elif has_default:
                final_kwargs[param.name] = param.default
            else:
                raise ValueError(f"Cannot resolve required dependency {annotation} for parameter {param.name}")

        return cls(**final_kwargs)

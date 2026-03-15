import inspect
import threading
from typing import Any, Callable, List, Optional, Self, Type, TypeVar, Union, cast, get_args, get_origin, get_type_hints

from ._enums import Lifetime, Priority
from ._registration import _Registration, _Registrations

T = TypeVar("T")
R = TypeVar("R")


class _Sentinel:
    def __repr__(self) -> str:
        return "REQUIRED"


REQUIRED: _Sentinel = _Sentinel()


class Binding[T]:
    def __init__(self, di: "DI", cls: Type[T], lifetime: Lifetime, priority: Priority) -> None:
        self._di = di
        self._cls = cls
        self._lifetime = lifetime
        self._priority = priority

    def implementation(self, impl: Type[T]) -> None:
        self._di._register(self._cls, _Registration(self._lifetime, self._priority, lambda: self._di.spawn(impl)))

    def factory(self, factory: Callable[..., T], *args: Any, **kwargs: Any) -> None:
        explicit: dict[str, Any] = dict(kwargs)
        if args:
            sig = inspect.signature(factory)
            params = list(sig.parameters.values())
            explicit = {p.name: v for p, v in zip(params, args, strict=False)} | explicit
        self._di._register(self._cls, _Registration(self._lifetime, self._priority, self._di.satisfy(factory, **explicit)))


class DI:
    def __init__(self) -> None:
        self._registry: dict[Type, _Registrations] = {}
        self._lock_registry_access = threading.Lock()
        self._signature_cache: dict[Any, inspect.Signature] = {}
        self._type_name_cache: dict[str, Type] = {}

    def _resolve_type(self, key: Type[T] | str) -> Type[T]:
        if isinstance(key, str):
            if key not in self._type_name_cache:
                found = next((t for t in self._registry if t.__name__ == key), None)
                if found is None:
                    raise ValueError(f"Cannot resolve type from string '{key}' - no matching type registered")
                self._type_name_cache[key] = found
            return self._type_name_cache[key]
        return key

    def register(self, cls: Type[T] | str, lifetime: Lifetime = Lifetime.SINGLETON, priority: Priority = Priority.LOW) -> Binding[T]:
        resolved_cls = cast(Type[T], self._resolve_type(cls)) if isinstance(cls, str) else cls
        return Binding(self, resolved_cls, lifetime=lifetime, priority=priority)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        with self._lock_registry_access:
            self._registry.clear()
        self._signature_cache.clear()
        self._type_name_cache.clear()

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

    def _try_resolve_annotation(self, annotation: Any, has_default: bool, default: Any) -> tuple[bool, Any]:
        if annotation is DI or (isinstance(annotation, type) and issubclass(annotation, DI)):
            return True, self

        origin = get_origin(annotation)

        if origin is list:
            type_args = get_args(annotation)
            return True, self.resolve_many(type_args[0]) if type_args else []

        if origin is Union:
            type_args = get_args(annotation)
            if type(None) in type_args:
                non_none_type = next(t for t in type_args if t is not type(None))
                resolved = self.resolve(non_none_type)
                if resolved is not None:
                    return True, resolved
                return True, default if has_default else None

        resolved = self.resolve(annotation)
        if resolved is not None:
            return True, resolved
        if has_default:
            return True, default
        return False, None

    def _resolve_kwargs(self, fn: Callable, skip_self: bool, explicit_kwargs: dict[str, Any]) -> dict[str, Any]:
        if fn not in self._signature_cache:
            self._signature_cache[fn] = inspect.signature(fn)
        sig = self._signature_cache[fn]

        hints_target = fn.__init__ if isinstance(fn, type) else fn
        try:
            type_hints = get_type_hints(hints_target)
        except Exception:
            type_hints = {}

        required_params = {k for k, v in explicit_kwargs.items() if v is REQUIRED}
        final_kwargs = {k: explicit_kwargs[k] for k in explicit_kwargs.keys() - required_params}
        params = list(sig.parameters.values())[1 if skip_self else 0:]

        for param in params:
            if param.name in final_kwargs or param.name in required_params:
                continue

            annotation = type_hints.get(param.name, param.annotation)
            if annotation == inspect.Parameter.empty:
                continue

            has_default = param.default != inspect.Parameter.empty
            ok, value = self._try_resolve_annotation(annotation, has_default, param.default)
            if not ok:
                raise ValueError(f"Cannot resolve required dependency {annotation} for parameter {param.name}")
            final_kwargs[param.name] = value

        return final_kwargs

    def spawn(self, cls: Type[T], *args: Any, **kwargs: Any) -> T:
        fn = cls.__init__
        if args:
            if fn not in self._signature_cache:
                self._signature_cache[fn] = inspect.signature(fn)
            params = list(self._signature_cache[fn].parameters.values())[1:]
            kwargs = {p.name: v for p, v in zip(params, args, strict=False)} | kwargs
        return cls(**self._resolve_kwargs(fn, skip_self=True, explicit_kwargs=kwargs))

    def satisfy(self, fn: Callable[..., R], **kwargs: Any) -> Callable[..., R]:
        resolved_kwargs = self._resolve_kwargs(fn, skip_self=False, explicit_kwargs=kwargs)

        def wrapper(**override: Any) -> R:
            return fn(**resolved_kwargs | override)

        return wrapper

    def scope(self) -> "DI":
        return _ScopedDI(self)


class _ScopedDI(DI):
    def __init__(self, parent: DI) -> None:
        super().__init__()
        self._parent = parent

    def _resolve_type(self, key: Type[T] | str) -> Type[T]:
        if isinstance(key, str):
            if key not in self._type_name_cache:
                found = next((t for t in self._registry if t.__name__ == key), None)
                if found is None:
                    return self._parent._resolve_type(key)
                self._type_name_cache[key] = found
            return self._type_name_cache[key]
        return key

    def resolve(self, key: Type[T] | str) -> Optional[T]:
        resolved_key = self._resolve_type(key) if isinstance(key, str) else key
        with self._lock_registry_access:
            registrations = self._registry.get(resolved_key)
        if registrations is not None:
            return cast(T, registrations.resolve_first())
        return self._parent.resolve(key)

    def resolve_many(self, key: Type[T] | str) -> List[T]:
        resolved_key = self._resolve_type(key) if isinstance(key, str) else key
        with self._lock_registry_access:
            registrations = self._registry.get(resolved_key)
        scoped_results: List[T] = registrations.resolve_all() if registrations is not None else []
        parent_results: List[T] = self._parent.resolve_many(key)
        return scoped_results + parent_results

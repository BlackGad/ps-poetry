# Overview

PS DI is a lightweight, thread-safe dependency injection container for Python. It provides a `DI` class that manages service registration, resolution, and automatic constructor injection. Registrations support singleton and transient lifetimes, priority-based ordering, and resolution by type or string name.

# Installation

```bash
pip install ps-di
```

Or with Poetry:

```bash
poetry add ps-di
```

# Quick Start

```python
from ps.di import DI, Lifetime

di = DI()

di.register(Logger).factory(Logger, "app")
di.register(UserRepository, Lifetime.TRANSIENT).implementation(UserRepository)

repo = di.resolve(UserRepository)
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-di/basic_usage_example.py)

# Register Services

The `register` method accepts a type (or string key), an optional `Lifetime`, and an optional `Priority`. It returns a `Binding` object that configures how the service is created.

* `.factory(callable, *args, **kwargs)` — Registers a callable that produces the service. Positional and keyword arguments are forwarded to the callable on each resolution.
* `.implementation(cls)` — Registers a class whose constructor is invoked via `spawn`, allowing the container to inject known dependencies automatically.

```python
from ps.di import DI, Lifetime

di = DI()

# Singleton (default) — one shared instance
di.register(Logger).factory(Logger, "app")

# Transient — new instance on every resolve
di.register(UserRepository, Lifetime.TRANSIENT).implementation(UserRepository)
```

`Lifetime` values:

* `SINGLETON` — The factory is called once; all subsequent resolves return the same instance. This is the default.
* `TRANSIENT` — The factory is called on every resolve, producing a new instance each time.

# Resolve Services

Use `resolve` to retrieve the highest-priority registration for a type, or `resolve_many` to retrieve all registrations ordered by priority.

```python
service = di.resolve(Logger)          # Logger | None
all_loggers = di.resolve_many(Logger) # list[Logger]
```

`resolve` returns `None` when no registration exists for the requested type. `resolve_many` returns an empty list in that case.

Both methods also accept a string type name instead of a class:

```python
service = di.resolve("Logger")
```

String resolution matches against the `__name__` attribute of registered types and raises `ValueError` when no match is found.

# Priority

Each registration carries a `Priority` that determines its position relative to other registrations for the same type. Higher-priority registrations are resolved first by `resolve` and appear earlier in the list returned by `resolve_many`.

```python
from ps.di import DI, Priority

di = DI()

di.register(NotificationService, priority=Priority.LOW).factory(NotificationService, "email")
di.register(NotificationService, priority=Priority.HIGH).factory(NotificationService, "sms")
di.register(NotificationService, priority=Priority.MEDIUM).factory(NotificationService, "push")

primary = di.resolve(NotificationService)  # sms (HIGH wins)
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-di/priority_example.py)

`Priority` values: `LOW` (default), `MEDIUM`, `HIGH`. When multiple registrations share the same priority, the most recently registered one wins.

# Spawn Objects

`spawn` instantiates a class without registering it, injecting constructor dependencies from the container automatically. It inspects type hints on `__init__` parameters and resolves them as follows:

* A parameter typed as `DI` or a subclass of `DI` receives the container itself.
* A parameter typed as `List[T]` receives the result of `resolve_many(T)`.
* A parameter typed as `Optional[T]` receives the result of `resolve(T)`, falling back to the default value when nothing is registered.
* Any other typed parameter receives the result of `resolve(T)`. If `resolve` returns `None` and no default exists, `spawn` raises `ValueError`.

Positional and keyword arguments passed to `spawn` override automatic resolution:

```python
from ps.di import DI

di = DI()
di.register(Logger).factory(Logger, "app")

repo = di.spawn(UserRepository)                       # Logger injected from container
repo = di.spawn(UserRepository, logger=custom_logger)  # explicit override
```

# Thread Safety

All registration and resolution operations are protected by internal locks. Singleton creation uses double-checked locking so the factory is called exactly once even under concurrent access. Transient registrations produce independent instances per call with no shared mutable state.

# Overview

The `ps-plugin-core` package is the core Poetry application plugin. It registers itself as a `poetry.application.plugin` entry point and acts as the host for any number of plugin modules. On activation, the plugin reads the project's `[tool.ps-plugin]` configuration, discovers installed modules via the `ps.module` entry-point group, instantiates them through a built-in dependency injection container, and dispatches lifecycle events to each active module.

# Installation

Declare the plugin as a required Poetry plugin in your project's `pyproject.toml`:

```toml
[tool.poetry.requires-plugins]
ps-plugin-core = "*"
```

Then run `poetry install` to install it locally for the project.

Alternatively, install globally as a Poetry plugin:

```bash
poetry self add ps-plugin-core
```

# Quick Start

The plugin activates automatically whenever the `[tool.ps-plugin]` section is present in your project's `pyproject.toml`. Adding any option to this section is sufficient:

```toml
[tool.ps-plugin]
```

All installed modules registered under the `ps.module` entry-point group are discovered and loaded. Use the `enabled = false` setting to explicitly opt out.

# Plugin Configuration

All plugin settings reside in the `[tool.ps-plugin]` section of `pyproject.toml`:

* `enabled` (`bool`) — Safety switch to disable the plugin for a project. The plugin activates whenever the `[tool.ps-plugin]` section is present regardless of other settings. Set to `false` to suppress activation.
* `host-project` (`str`) — Relative path to a host project. When set, the plugin reads configuration from that project's `pyproject.toml` and merges it with the current project's settings.
* `modules` (`list[str]`) — Names of plugin modules to activate. Modules are instantiated in the declared order. When omitted, no modules are loaded.

```toml
[tool.ps-plugin]
modules = ["delivery", "check"]
```

# Module Loading

Modules are discovered by scanning the `ps.module` entry-point group at runtime. The plugin inspects every loaded object for functions whose names match the pattern `poetry_<event>` or `poetry_<event>_<suffix>`, where `<event>` is one of: `activate`, `command`, `error`, `terminate`, `signal`.

> **Note:** Module discovery relies on `importlib.metadata`, which reads `entry_points.txt` from installed distribution metadata in `site-packages`. Entry points declared in a `pyproject.toml` with `package-mode = false` are **never registered** because that project is not installed as a distribution. Only packages installed via `pip install -e .` or `poetry install` (with `package-mode = true`) produce the `.dist-info` directory that makes their entry points discoverable.

An entry point may resolve to:

* **A class** — instance methods matching the pattern form one module; static/class methods with a suffix form additional modules grouped by suffix.
* **A Python module (namespace)** — all classes and module-level functions inside it are scanned recursively.
* **A plain function** — must have a suffix (e.g. `poetry_command_delivery`).

## Module naming

| Source | Name resolution |
| --- | --- |
| Class with `name` attribute | Value of `cls.name` |
| Class without `name` attribute | `cls.__name__` |
| Static/class method or global function | The suffix portion after `poetry_<event>_` |

## Collision detection

When two or more distributions expose a module with the same name, all conflicting modules are skipped and a warning is printed. Non-conflicting modules from all distributions remain available.

When a `modules` list is present in configuration, only those modules are loaded (in the declared order). When the list is absent, no modules are loaded.

# Function Naming Convention

A module class declares its capabilities through method naming. Each function name maps to a specific Poetry console lifecycle event:

* `poetry_activate(application) -> None | bool` — Called once during plugin activation. Returning `False` removes the module from all subsequent event listeners. Any other return value (including `None`) keeps the module active.
* `poetry_command(event) -> None` — Called on every Poetry console command event.
* `poetry_terminate(event) -> None` — Called after a Poetry command finishes.
* `poetry_error(event) -> None` — Called when a Poetry command raises an unhandled error.
* `poetry_signal(event) -> None` — Called on OS signal events during command execution.

A single module class may define any combination of these methods. Optional typing protocols (`PoetryActivateProtocol`, `PoetryCommandProtocol`, etc.) are available in `ps.plugin.sdk.events` for IDE support but are not required.

# Dependency Injection

Every handler function is invoked through the `DI.satisfy` wrapper, which inspects the function signature and injects registered types as keyword arguments automatically. Constructor parameters of class-based modules are resolved the same way via `DI.spawn`.

The following types are pre-registered by the plugin host and can be used as function/constructor parameters:

| Type | Import | Description |
| --- | --- | --- |
| `IO` | `from cleo.io.io import IO` | Cleo IO for the current Poetry invocation |
| `Application` | `from poetry.console.application import Application` | The active Poetry application instance |
| `Environment` | `from ps.plugin.sdk.environment import Environment` | Resolved project environment with host/workspace access |
| `PluginSettings` | `from ps.plugin.sdk.settings import PluginSettings` | Parsed `[tool.ps-plugin]` settings |
| `EventDispatcher` | `from cleo.events.event_dispatcher import EventDispatcher` | The Cleo event dispatcher |

Inside event handlers (`poetry_command`, `poetry_error`, `poetry_terminate`, `poetry_signal`), additional types are registered in a scoped DI container:

| Type | Import | Description |
| --- | --- | --- |
| `ConsoleCommandEvent` | `from cleo.events.console_command_event import ConsoleCommandEvent` | The current command event (for `poetry_command`) |
| `ConsoleTerminateEvent` | `from cleo.events.console_terminate_event import ConsoleTerminateEvent` | The terminate event (for `poetry_terminate`) |
| `ConsoleErrorEvent` | `from cleo.events.console_error_event import ConsoleErrorEvent` | The error event (for `poetry_error`) |
| `ConsoleSignalEvent` | `from cleo.events.console_signal_event import ConsoleSignalEvent` | The signal event (for `poetry_signal`) |

Use `DI.register` to bind additional types from within `poetry_activate` and `DI.resolve` or `DI.resolve_many` to retrieve them in other modules.

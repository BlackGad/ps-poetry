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

Modules are distributed as Python packages that register a class under the `ps.module` entry-point group. The plugin scans this group at runtime using `importlib.metadata`, inspects each discovered class for supported lifecycle protocols, and instantiates only those that implement at least one known protocol.

When a `modules` list is present in the configuration, the plugin activates exactly those modules in the user-defined order and ignores the rest. When the list is absent, no modules are loaded.

# Lifecycle Protocols

A module class declares its capabilities by implementing one or more protocols from `ps.plugin.sdk.events`. Each protocol maps to a specific Poetry console lifecycle event:

* `ActivateProtocol` — `handle_activate(application) -> bool`. Called once during plugin activation. Returning `False` removes the module from all subsequent event listeners.
* `ListenerCommandProtocol` — `handle_command(event, event_name, dispatcher)`. Called on every Poetry console command event.
* `ListenerTerminateProtocol` — `handle_terminate(event, event_name, dispatcher)`. Called after a Poetry command finishes successfully.
* `ListenerErrorProtocol` — `handle_error(event, event_name, dispatcher)`. Called when a Poetry command raises an unhandled error.
* `ListenerSignalProtocol` — `handle_signal(event, event_name, dispatcher)`. Called on OS signal events received during command execution.

A single module class may implement any combination of these protocols.

# Dependency Injection

The plugin creates a `DI` container (defined in `ps.plugin.sdk.di`) that is shared across all module instances. Constructor parameters of module classes are resolved automatically by type when the module is instantiated via `DI.spawn`. The following types are pre-registered by the plugin host:

* `IO` — The Cleo IO object for the current Poetry invocation.
* `Application` — The active Poetry `Application` instance.
* `Environment` — The resolved project environment, providing access to the host and workspace projects.
* `PluginSettings` — The parsed `[tool.ps-plugin]` settings for the current project.

Use `DI.register` to bind additional types from within a module's `handle_activate` implementation and `DI.resolve` or `DI.resolve_many` to retrieve them in other modules or components.

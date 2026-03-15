# Overview

The `ps-plugin-sdk` package provides the shared abstractions, models, protocols, and helpers for building Poetry plugin modules. It defines data structures for representing projects and their dependencies, protocols for plugin lifecycle events, a dependency injection interface, and utility functions for reading `pyproject.toml` documents.

Plugin modules depend on this package to interact with the Poetry plugin host without coupling to the internal plugin implementation.

# Installation

```bash
pip install ps-plugin-sdk
```

Or with Poetry:

```bash
poetry add ps-plugin-sdk
```

# Quick Start

Parse a `pyproject.toml` document to extract project metadata:

```python
from tomlkit import parse
from ps.plugin.sdk import parse_name_from_document, parse_version_from_document

content = '[project]\nname = "my-package"\nversion = "1.2.3"\n'
document = parse(content)

print(parse_name_from_document(document).value)
print(parse_version_from_document(document).value)
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-plugin-sdk/basic_usage_example.py)

# Parse TOML Documents

The SDK provides helpers to extract structured data from `TOMLDocument` objects (parsed with `tomlkit`). All parse functions accept a document created by `tomlkit.parse()` and return either a typed model or a `TomlValue` pointing to the located data.

* `parse_name_from_document(document)` — Returns a `TomlValue` referencing the project name, scanning both `[project]` (PEP 621) and `[tool.poetry]` sections. Prefers PEP 621 when both are present.
* `parse_version_from_document(document)` — Returns a `TomlValue` referencing the project version from `[project]` or `[tool.poetry]`.
* `parse_sources_from_document(document)` — Returns a list of `ProjectFeedSource` objects from the `[[tool.poetry.source]]` array.
* `parse_plugin_settings_from_document(document)` — Returns a `PluginSettings` instance parsed from `[tool.ps-plugin]`. Returns `PluginSettings(enabled=False)` when that section is absent.
* `parse_project(project_path)` — Reads and parses a `pyproject.toml` file from disk, returning a fully populated `Project` model. Returns `None` if the file does not exist.

# Parse Dependencies

Use `parse_dependencies_from_document(document, project_path)` to extract all declared dependencies from a `TOMLDocument`. The function supports both PEP 621 format (`project.dependencies` as an array of PEP 508 strings) and Poetry format (`tool.poetry.dependencies` and named dependency groups).

Each returned `ProjectDependency` exposes attributes common to both formats: `name`, `group`, `optional`, `markers`, `extras`, `source`, `path`, `git`, `url`, `branch`, `tag`, `rev`, and `develop`. The `version` property retrieves the raw version constraint string, and `version_constraint` converts it to a `packaging.specifiers.SpecifierSet`. Call `update_version(constraint)` to overwrite the constraint directly in the backing `TOMLDocument`.

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-plugin-sdk/parse_dependencies_example.py)

# Project Model

The `Project` model represents a single Poetry project loaded from a `pyproject.toml` file:

```python
project.name.value        # str | None  — project name
project.version.value     # str | None  — project version
project.path              # Path        — absolute path to pyproject.toml
project.dependencies      # list[ProjectDependency]
project.sources           # list[ProjectFeedSource]
project.plugin_settings   # PluginSettings
project.save()            # write the document back to disk
```

The `document` field holds the live `TOMLDocument`. Modifying values through `TomlValue.set()` and calling `project.save()` writes changes back to disk while preserving the original TOML formatting.

Each `ProjectFeedSource` captures `name`, optional `url`, and an optional `SourcePriority` value (`default`, `primary`, `secondary`, `supplemental`, or `explicit`).

# Plugin Settings

`PluginSettings` reflects the `[tool.ps-plugin]` section of a `pyproject.toml` file:

* `enabled` (`bool | None`) — Whether the plugin is active for this project. Defaults to `True` when the section is present and `False` when it is absent.
* `host_project` (`Path | None`) — Relative path to a host project that owns the plugin configuration.
* `modules` (`list[str] | None`) — Names of plugin modules to load.

Additional fields declared in the TOML section are preserved under `model_extra` due to `extra="allow"`.

# TOML Value

`TomlValue` locates a TOML entry within a `TOMLDocument` by navigating a dotted-key path. It is used throughout the SDK to provide stable references to document values that can later be read or overwritten in place.

* `value` — Returns the current value at the resolved path, or `None` if not found.
* `exists` — Returns `True` if the path was resolved successfully during construction.
* `set(new_value)` — Overwrites the value in the underlying document without altering surrounding TOML formatting.
* `TomlValue.locate(document, candidates)` — Resolves the first matching dotted path from an ordered list of candidates and returns a `TomlValue`. Falls back to the first candidate path when none match.

# Environment

`Environment` manages a collection of `Project` objects representing a multi-project workspace. Initialize it with the path to any `pyproject.toml` and it discovers the full project graph automatically:

```python
from pathlib import Path
from ps.plugin.sdk import Environment

env = Environment(Path("./pyproject.toml"))

for project in env.projects:
    print(project.name.value)

print(env.host_project.name.value)
```

When initialized, `Environment` loads the entry project, then recursively follows local path dependencies where `develop` is not `False`. It also respects `host-project` references in `[tool.ps-plugin]`, loading and promoting the referenced project to host status. The `backup_projects` and `restore_projects` methods provide snapshot and rollback support for workflows that mutate `pyproject.toml` files.

# Protocols

The SDK defines structural protocols (using `typing_extensions.Protocol`) that describe how plugin modules interact with the Poetry plugin host. Modules implement one or more of these protocols to participate in plugin lifecycle events. All listener protocols are `@runtime_checkable`, enabling `isinstance` checks at runtime.

* `ActivateProtocol` — Implement `handle_activate(application)` to run setup code when the Poetry application activates.
* `ListenerCommandProtocol` — Implement `handle_command(event, event_name, dispatcher)` to intercept console commands before they execute.
* `ListenerErrorProtocol` — Implement `handle_error(event, event_name, dispatcher)` to handle errors raised during command execution.
* `ListenerSignalProtocol` — Implement `handle_signal(event, event_name, dispatcher)` to respond to OS signals received during command execution.
* `ListenerTerminateProtocol` — Implement `handle_terminate(event, event_name, dispatcher)` to run cleanup after a console command completes.
* `NameAwareProtocol` — Requires a class-level `name: ClassVar[str]` attribute. Used as a base for identifiable components such as `ICheck`.

# Dependency Injection

The SDK re-exports the `DI` class and related types (`Binding`, `Lifetime`, `Priority`) from the `ps-di` library. Plugin modules receive a `DI` instance and use it to register and resolve services. See the [ps-di README](../libraries/di/README.md) for the full documentation.

* `register(cls, lifetime, priority)` — Registers a class or string key with an optional lifetime and priority. Returns a `Binding` that configures the implementation via `.implementation(impl)` or a factory via `.factory(factory, *args, **kwargs)`.
* `resolve(key)` — Returns the highest-priority registered instance for `key`, or `None`.
* `resolve_many(key)` — Returns all registered instances for `key`.
* `spawn(cls, *args, **kwargs)` — Instantiates `cls` directly without registering it, injecting known dependencies from the container.

`Lifetime` values: `SINGLETON` (one shared instance per container) and `TRANSIENT` (new instance on every resolve). `Priority` values: `LOW`, `MEDIUM`, and `HIGH` — higher-priority bindings win when multiple registrations exist for the same key.

The `ICheck` abstract class extends `NameAwareProtocol` and serves as the base for check implementations. Subclasses implement `check(io, projects, fix)` to perform a named check and return an optional exception on failure. The `can_check(projects)` method allows a check to declare itself inapplicable to a given project list.

`IVersionTokenResolver` extends `NameAwareProtocol` and defines the interface for registering custom token resolvers with the delivery module. Subclasses declare a `name: ClassVar[str]` identifying the token source, and implement `get_resolver()` to return the resolver callable that the delivery module registers in its expression factory. Register implementations using `di.register(IVersionTokenResolver)` so the delivery module discovers them automatically via `di.resolve_many(IVersionTokenResolver)`.

# Command Helpers

The command helpers assist modules that extend Poetry commands with additional options or arguments.

* `ensure_argument(command, argument)` — Appends `argument` to `command.arguments` if an argument with the same name is not already present. Returns `True` if the argument was added.
* `ensure_option(command, option)` — Appends `option` to `command.options` if an option with the same name is not already present. Returns `True` if the option was added.
* `CommandOptionsProtocol` — Structural protocol describing an object with `options: list[Option]` and `arguments: list[Argument]` attributes, compatible with Cleo command objects.
* `filter_projects(inputs, projects)` — Filters an iterable of `Project` objects against a list of name or path strings. Each input is matched by exact project name or by path containment. When `inputs` is empty, all projects are returned unchanged.

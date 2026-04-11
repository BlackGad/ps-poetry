# Overview

[![PyPI](https://img.shields.io/pypi/v/ps-plugin-sdk)](https://pypi.org/project/ps-plugin-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/ps-plugin-sdk)](https://pypi.org/project/ps-plugin-sdk/)
[![License](https://img.shields.io/pypi/l/ps-plugin-sdk)](https://pypi.org/project/ps-plugin-sdk/)

The `ps-plugin-sdk` package provides the shared abstractions, models, protocols, and helpers for building Poetry plugin modules. It defines data structures for representing projects and their dependencies, protocols for plugin lifecycle events, a dependency injection interface, and utility functions for reading `pyproject.toml` documents.

Plugin modules depend on this package to interact with the Poetry plugin host without coupling to the internal plugin implementation.

For working project examples, see the [ps-poetry-examples](https://github.com/BlackGad/ps-poetry-examples) repository.

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
from ps.plugin.sdk.project import parse_name_from_document, parse_version_from_document

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
* `parse_source_dirs_from_document(document, project_path)` — Returns a list of resolved `Path` objects for package source directories declared in `[[tool.poetry.packages]]`. Falls back to the project directory when no packages entries are present.

# Parse Dependencies

Use `parse_dependencies_from_document(document, project_path)` to extract all declared dependencies from a `TOMLDocument`. The function supports both PEP 621 format (`project.dependencies` as an array of PEP 508 strings) and Poetry format (`tool.poetry.dependencies` and named dependency groups).

Each returned `ProjectDependency` exposes attributes common to both formats: `name`, `group`, `optional`, `python`, `markers`, `extras`, `source`, `path`, `git`, `url`, `branch`, `tag`, `rev`, and `develop`. The `version` property retrieves the raw version constraint string, `version_constraint` converts it to a `packaging.specifiers.SpecifierSet`, and `resolved_project_path` resolves the `path` field to the absolute path of the dependency's `pyproject.toml` file, returning `None` when `path` is not set. Call `update_version(constraint)` to overwrite the constraint directly in the backing `TOMLDocument`.

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-plugin-sdk/parse_dependencies_example.py)

# Project Model

The `Project` model represents a single Poetry project loaded from a `pyproject.toml` file:

```python
project.name.value        # str | None  — project name
project.version.value     # str | None  — project version
project.path              # Path        — absolute path to pyproject.toml
project.dependencies      # list[ProjectDependency]
project.sources           # list[ProjectFeedSource]
project.source_dirs       # list[Path]  — resolved source package directories
project.plugin_settings   # PluginSettings
project.save()            # write the document back to disk
project.add_dependency(name, constraint=None, group=None)
project.add_development_dependency(name, path, group=None)
```

The `document` field holds the live `TOMLDocument`. Modifying values through `TomlValue.set()` and calling `project.save()` writes changes back to disk while preserving the original TOML formatting.

`add_dependency(name, constraint=None, group=None)` inserts a version-pinned dependency into `[tool.poetry.dependencies]` or the named group and returns the new `ProjectDependency`. `add_development_dependency(name, path, group=None)` inserts a local path dependency with `develop = true` relative to the project directory.

Each `ProjectFeedSource` captures `name`, optional `url`, and an optional `SourcePriority` value (`default`, `primary`, `secondary`, `supplemental`, or `explicit`).

# Plugin Settings

`PluginSettings` reflects the `[tool.ps-plugin]` section of a `pyproject.toml` file:

* `NAME` (`ClassVar[str]`) — The section name constant `"ps-plugin"` used to locate settings in a TOML document.
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
from ps.plugin.sdk.project import Environment

env = Environment(Path("./pyproject.toml"))

for project in env.projects:
    print(project.name.value)

print(env.host_project.name.value)
```

When initialized, `Environment` loads the entry project, then recursively follows local path dependencies where `develop` is not `False`. It also respects `host-project` references in `[tool.ps-plugin]`, loading and promoting the referenced project to host status. The `backup_projects` and `restore_projects` methods provide snapshot and rollback support for workflows that mutate `pyproject.toml` files.

* `add_project(project_path, is_host=False)` — Loads the project at `project_path` into the environment graph, recursively following its local path dependencies. Promotes the project to host status when `is_host=True`. Returns the loaded `Project`.
* `project_dependencies(project)` — Returns a `list[Project]` containing every project in the environment that `project` declares as a local path dependency.
* `sorted_projects(projects)` — Returns the provided projects in topological order so that each dependency appears before the projects that depend on it.

# Protocols

The SDK provides optional `@runtime_checkable` typing protocols in `ps.plugin.sdk.events` for IDE support and type checking. These protocols describe the expected function signatures for plugin module lifecycle hooks but are **not required** — the plugin host discovers handlers by function name, not by protocol implementation.

* `PoetryActivateProtocol` — `poetry_activate(application) -> bool`. Called during plugin activation. Return `False` to disable the module.
* `PoetryCommandProtocol` — `poetry_command(event, dispatcher) -> None`. Called on console command events.
* `PoetryErrorProtocol` — `poetry_error(event, dispatcher) -> None`. Called on command errors.
* `PoetrySignalProtocol` — `poetry_signal(event, dispatcher) -> None`. Called on OS signal events.
* `PoetryTerminateProtocol` — `poetry_terminate(event, dispatcher) -> None`. Called after command completion.

# Command Helpers

The command helpers assist modules that extend Poetry commands with additional options or arguments.

* `ensure_argument(command, argument)` — Appends `argument` to `command.arguments` if an argument with the same name is not already present. Returns `True` if the argument was added.
* `ensure_option(command, option)` — Appends `option` to `command.options` if an option with the same name is not already present. Returns `True` if the option was added.
* `CommandOptionsProtocol` — Structural protocol describing an object with `options: list[Option]` and `arguments: list[Argument]` attributes, compatible with Cleo command objects.
* `filter_projects(inputs, projects)` — Filters an iterable of `Project` objects against a list of name or path strings. Each input is matched by exact project name or by path containment. When `inputs` is empty, all projects are returned unchanged.

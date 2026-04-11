# Overview

[![License](https://img.shields.io/pypi/l/ps-plugin-core)](https://pypi.org/project/ps-plugin-core/)
[![Python](https://img.shields.io/pypi/pyversions/ps-plugin-core)](https://pypi.org/project/ps-plugin-core/)

| Package | Version |
| --- | --- |
| ps-plugin-core | [![PyPI](https://img.shields.io/pypi/v/ps-plugin-core)](https://pypi.org/project/ps-plugin-core/) |
| ps-plugin-sdk | [![PyPI](https://img.shields.io/pypi/v/ps-plugin-sdk)](https://pypi.org/project/ps-plugin-sdk/) |
| ps-plugin-module-check | [![PyPI](https://img.shields.io/pypi/v/ps-plugin-module-check)](https://pypi.org/project/ps-plugin-module-check/) |
| ps-plugin-module-delivery | [![PyPI](https://img.shields.io/pypi/v/ps-plugin-module-delivery)](https://pypi.org/project/ps-plugin-module-delivery/) |
| ps-dependency-injection | [![PyPI](https://img.shields.io/pypi/v/ps-dependency-injection)](https://pypi.org/project/ps-dependency-injection/) |
| ps-version | [![PyPI](https://img.shields.io/pypi/v/ps-version)](https://pypi.org/project/ps-version/) |
| ps-token-expressions | [![PyPI](https://img.shields.io/pypi/v/ps-token-expressions)](https://pypi.org/project/ps-token-expressions/) |

This repository contains the `ps-poetry` Poetry plugin and its ecosystem. The plugin extends Poetry with a modular architecture: a lightweight core host discovers and loads independently packaged modules at runtime, dispatching lifecycle events to each active module. Two modules are provided — `check` and `delivery` — and three support libraries are available for use by modules and other consumers.

# Plugin

The `ps-plugin-core` package is the core Poetry application plugin host. It registers itself as a `poetry.application.plugin` entry point, reads the project's `[tool.ps-plugin]` configuration, discovers installed modules via the `ps.module` entry-point group, instantiates them through a built-in dependency injection container, and dispatches lifecycle events to each active module.

[View ps-plugin-core documentation](https://github.com/BlackGad/ps-poetry/blob/main/plugin/README.md)

# Modules

## Check

The `ps-plugin-module-check` module extends Poetry's built-in `check` command with a configurable sequence of quality checks across all projects in a monorepo. It provides seven built-in checkers — `poetry`, `environment`, `imports`, `ruff`, `pylint`, `pytest`, and `pyright` — with support for automatic fixing and per-project configuration.

[View ps-plugin-module-check documentation](https://github.com/BlackGad/ps-poetry/blob/main/modules/check/README.md)

## Delivery

The `ps-plugin-module-delivery` module automates building and publishing packages across a monorepo. It extends Poetry's `build` and `publish` commands with unified version stamping, dependency constraint resolution, and topologically-ordered publish waves. A standalone `delivery` command displays the planned build and publish dependency tree without executing it.

[View ps-plugin-module-delivery documentation](https://github.com/BlackGad/ps-poetry/blob/main/modules/delivery/README.md)

# Libraries

## ps-dependency-injection

`ps-dependency-injection` is a lightweight, thread-safe dependency injection container for Python. It provides a `DI` class that manages service registration, resolution, and automatic constructor injection. Registrations support singleton and transient lifetimes, priority-based ordering, and resolution by type or string name. The plugin host and all modules use `ps-dependency-injection` to wire their services.

[View ps-dependency-injection documentation](https://github.com/BlackGad/ps-poetry/blob/main/libraries/di/README.md)

## ps-version

`ps-version` is a version parsing, comparison, and formatting library. It automatically detects the version format (PEP 440, SemVer, NuGet, CalVer, or Loose) and parses version strings into a unified `Version` dataclass that supports standard comparison operators and cross-format output. The delivery module uses `ps-version` to parse and validate build versions.

[View ps-version documentation](https://github.com/BlackGad/ps-poetry/blob/main/libraries/version/README.md)

## ps-token-expressions

`ps-token-expressions` is a token-based string templating and expression evaluation library. It resolves `{key:arg}` tokens against dict, function, list, or object resolvers, supports conditional matching with logical and comparison operators, and provides fallback values for unresolved tokens. The delivery module uses `ps-token-expressions` to evaluate configurable version and path expressions.

[View ps-token-expressions documentation](https://github.com/BlackGad/ps-poetry/blob/main/libraries/token_expressions/README.md)

# SDK

The `ps-plugin-sdk` package provides the shared abstractions, models, protocols, and helpers for building Poetry plugin modules. It defines data structures for representing projects and their dependencies, protocols for plugin lifecycle events, and utility functions for reading `pyproject.toml` documents. Plugin modules depend on this package to interact with the Poetry plugin host without coupling to the internal plugin implementation.

[View ps-plugin-sdk documentation](https://github.com/BlackGad/ps-poetry/blob/main/sdk/README.md)

# Examples

A dedicated repository with working project examples demonstrating plugin and module usage is available at [ps-poetry-examples](https://github.com/BlackGad/ps-poetry-examples).

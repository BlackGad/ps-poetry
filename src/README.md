# Overview

This repository contains the `ps-poetry` Poetry plugin and its ecosystem. The plugin extends Poetry with a modular architecture: a lightweight core host discovers and loads independently packaged modules at runtime, dispatching lifecycle events to each active module. Three modules are provided — `check`, `delivery`, and `monorepo` — and two support libraries are available for use by modules and other consumers.

# Plugin

The `ps-plugin-core` package is the Poetry application plugin host. It activates when a `[tool.ps-plugin]` section is present in `pyproject.toml`, discovers all installed modules registered under the `ps.module` entry-point group, and manages their lifecycle through a built-in dependency injection container.

[View ps-plugin-core documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/plugin/README.md)

# Modules

## Check

The `ps-plugin-module-check` module extends Poetry's built-in `check` command with a configurable sequence of quality checks across all projects in a monorepo. Available checkers include `poetry` (pyproject.toml validation), `ruff` (linting), `pylint`, `pytest` (test execution), and environment tool availability. The module supports `--fix` and `--continue-on-error` flags, and which checkers run for a given project is controlled by its `[tool.ps-plugin]` settings.

[View ps-plugin-module-check documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/modules/check/README.md)

## Delivery

The `ps-plugin-module-delivery` module automates building and publishing packages across a monorepo. It intercepts Poetry's `build` and `publish` commands, applies a unified build version via `--build-version`, resolves inter-project dependency ordering, and batches projects into sequenced publish waves. A standalone `delivery` command displays the planned build and publish dependency tree without executing it. Typical invocations are `poetry build -b 1.2.3` or `poetry publish -b 1.2.3`.

[View ps-plugin-module-delivery documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/modules/delivery/README.md)

## Monorepo

The `ps-plugin-module-monorepo` module makes standard Poetry commands (`install`, `lock`, `update`, `add`, `remove`) work correctly when run from a sub-package directory inside a monorepo. When invoked in a sub-project context, it transparently redirects the command to the monorepo root, ensuring the shared lockfile and virtual environment remain consistent regardless of the working directory.

[View ps-plugin-module-monorepo documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/modules/monorepo/README.md)

# Libraries

## ps-di

`ps-di` is a lightweight, thread-safe dependency injection container. It supports singleton and transient lifetimes, priority-based registration ordering, automatic constructor injection via `spawn`, and resolution by type or string name. The plugin host and all modules use `ps-di` to wire their services.

[View ps-di documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/libraries/di/README.md)

## ps-version

`ps-version` is a version parsing, comparison, and formatting library. It automatically detects the version format (PEP 440, SemVer, NuGet, CalVer, or Loose) and parses version strings into a unified `Version` dataclass that supports standard comparison operators and cross-format output. The delivery module uses `ps-version` to parse and validate build versions.

[View ps-version documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/libraries/version/README.md)

## ps-token-expressions

`ps-token-expressions` is a token-based string templating and expression evaluation library. It resolves `{key:arg}` tokens against dict, function, list, or object resolvers, supports conditional matching with logical and comparison operators, and provides fallback values for unresolved tokens. The delivery module uses `ps-token-expressions` to evaluate configurable version and path expressions.

[View ps-token-expressions documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/libraries/token_expressions/README.md)

# SDK

The `ps-plugin-sdk` package provides the shared abstractions, models, protocols, and helpers for building plugin modules. It defines the `ActivateProtocol` and listener protocols that modules implement to participate in plugin lifecycle events, TOML parsing helpers for reading `pyproject.toml` documents, the `Environment` and `Project` models for navigating a multi-project workspace, and the `ICheck` base class for check implementations.

[View ps-plugin-sdk documentation](https://github.com/BlackGad/ps-poetry/blob/main/src/sdk/README.md)

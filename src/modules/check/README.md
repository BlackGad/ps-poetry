# Overview

[![PyPI](https://img.shields.io/pypi/v/ps-plugin-module-check)](https://pypi.org/project/ps-plugin-module-check/)
[![Python](https://img.shields.io/pypi/pyversions/ps-plugin-module-check)](https://pypi.org/project/ps-plugin-module-check/)
[![License](https://img.shields.io/pypi/l/ps-plugin-module-check)](https://pypi.org/project/ps-plugin-module-check/)

The `ps-plugin-module-check` module extends Poetry's built-in `check` command with a configurable sequence of quality checks across all projects in a monorepo. It provides seven built-in checkers — `poetry`, `environment`, `imports`, `ruff`, `pylint`, `pytest`, and `pyright` — with support for automatic fixing and per-project configuration.

The module is registered as a `ps.module` entry point and activates when included in the host project's `[tool.ps-plugin]` configuration. Requires [`ps-plugin-core`](https://pypi.org/project/ps-plugin-core/) as the plugin host.

For working project examples, see the [ps-poetry-examples](https://github.com/BlackGad/ps-poetry-examples) repository.

# Installation

```bash
pip install ps-plugin-module-check
```

Or with Poetry:

```bash
poetry add ps-plugin-module-check
```

Enable it in the plugin configuration:

```toml
[tool.ps-plugin]
modules = ["ps-check"]
```

# Quick Start

Run all configured checks across all projects:

```bash
poetry check
```

Run checks on specific projects with automatic fixing:

```bash
poetry check my-package --fix
```

# Configuration

The module reads its settings from the `[tool.ps-plugin]` section of the host project's `pyproject.toml`. The `checks` field specifies which checkers to run and in what order.

```toml
[tool.ps-plugin]
checks = ["poetry", "environment", "ruff", "pytest"]
```

When `checks` is omitted or empty, no checkers are selected and the command exits immediately. Only checkers listed in `checks` are executed, and they run in the declared order.

# Command-Line Usage

The module extends Poetry's `check` command with additional arguments and options:

```bash
poetry check [INPUTS...] [--fix] [--continue-on-error]
```

* `INPUTS` — Optional list of project names or paths to check. When omitted, all discovered projects are checked. When running from a sub-project that differs from the host project, the sub-project is selected automatically.
* `--fix` / `-f` — Enable automatic fixing in checkers that support it (`ruff` and `imports`).
* `--continue-on-error` / `-c` — Continue checking remaining projects and checkers after a failure instead of stopping on the first error.

# Available Checks

## poetry

Runs Poetry's built-in `check` command on each target project independently, validating the `pyproject.toml` structure and metadata.

## environment

Validates consistency of package sources across all target projects. Detects two types of conflicts:

* **URL conflicts** — The same source name (case-insensitive) is declared with different URLs in different projects.
* **Priority conflicts** — The same source name is declared with different priority levels across projects.

This checker is validation-only and does not support automatic fixing.

## imports

Walks each project's source directories and collects all non-stdlib, non-relative imports using AST analysis. For each import, the checker verifies that the providing distribution is declared as a dependency of the project, either directly or transitively through local path dependencies.

Stdlib modules, `__future__` imports, and modules belonging to the project's own package are silently skipped. When a required distribution is not declared, the checker reports the missing dependency together with the file paths and line numbers where the import appears.

When the `--fix` flag is provided, the checker adds each missing dependency automatically. Local monorepo packages are preferred over PyPI packages and are added as development dependencies with a path reference. PyPI packages are added as regular dependencies with an unconstrained version specifier. Projects are greedily consolidated so that adding a single dependency covers as many missing imports as possible through its transitive closure.

## ruff

Runs the `ruff` linter on the collected source paths. When the `--fix` flag is provided, the `--fix` argument is forwarded to ruff to apply automatic corrections. This checker is only available when `ruff` is installed and accessible in PATH.

## pylint

Runs `pylint` on the collected source paths. This checker is only available when `pylint` is installed and accessible in PATH.

## pytest

Runs `pytest` on the collected source paths. This checker is only available when `pytest` is installed and accessible in PATH.

## pyright

Runs `pyright` on the collected source paths for static type checking. This checker is only available when `pyright` is installed and accessible in PATH. Auto-fixing is not supported.

# Custom Checks

`ICheck` is the abstract base class for implementing custom checkers. Subclasses implement `check(io, projects, fix)` to perform the check and return an optional exception on failure. The `can_check(projects)` method allows a checker to declare itself inapplicable to a given project list. Each subclass must declare a `name: ClassVar[str]` attribute that matches the name used in the `checks` configuration list.

Register custom implementations with the DI container using `di.register(ICheck)` inside `poetry_activate` so the check module discovers them automatically via `di.resolve_many(ICheck)`.

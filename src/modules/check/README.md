# Overview

The `ps-plugin-module-check` module extends Poetry's built-in `check` command with a configurable sequence of quality checks across all projects in a monorepo. It provides six built-in checkers — `poetry`, `environment`, `ruff`, `pylint`, `pytest`, and `pyright` — with support for automatic fixing and per-project configuration.

The module is registered as a `ps.module` entry point and activates when included in the host project's `[tool.ps-plugin]` configuration.

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
* `--fix` / `-f` — Enable automatic fixing in checkers that support it (currently only `ruff`).
* `--continue-on-error` / `-c` — Continue checking remaining projects and checkers after a failure instead of stopping on the first error.

# Available Checks

## poetry

Runs Poetry's built-in `check` command on each target project independently, validating the `pyproject.toml` structure and metadata.

## environment

Validates consistency of package sources across all target projects. Detects two types of conflicts:

* **URL conflicts** — The same source name (case-insensitive) is declared with different URLs in different projects.
* **Priority conflicts** — The same source name is declared with different priority levels across projects.

This checker is validation-only and does not support automatic fixing.

## ruff

Runs the `ruff` linter on the collected source paths. When the `--fix` flag is provided, the `--fix` argument is forwarded to ruff to apply automatic corrections. This checker is only available when `ruff` is installed and accessible in PATH.

## pylint

Runs `pylint` on the collected source paths. This checker is only available when `pylint` is installed and accessible in PATH.

## pytest

Runs `pytest` on the collected source paths. This checker is only available when `pytest` is installed and accessible in PATH.

## pyright

Runs `pyright` on the collected source paths for static type checking. This checker is only available when `pyright` is installed and accessible in PATH. Auto-fixing is not supported.

# Overview

The `ps-plugin-module-monorepo` module makes standard Poetry commands work correctly when run from a sub-package directory inside a monorepo. It intercepts commands such as `install`, `lock`, `update`, `add`, `remove`, and `env` and transparently redirects them to operate on the monorepo root, ensuring the shared lockfile and virtual environment remain consistent regardless of the working directory.

The module is registered as a `ps.module` entry point and activates when included in the host project's `[tool.ps-plugin]` configuration.

# Installation

```bash
pip install ps-plugin-module-monorepo
```

Or with Poetry:

```bash
poetry add ps-plugin-module-monorepo
```

Enable it in the plugin configuration:

```toml
[tool.ps-plugin]
modules = ["ps-monorepo"]
```

Each sub-package must reference the host project in its own `[tool.ps-plugin]` section:

```toml
[tool.ps-plugin]
host-project = "../.."
```

# Quick Start

With the module enabled, run any supported Poetry command from a sub-package directory and it will operate on the monorepo root automatically:

```bash
cd packages/my-library
poetry install    # installs at the monorepo root
poetry add httpx  # adds to the monorepo root
poetry lock       # locks at the monorepo root
```

# Intercepted Commands

The module activates only when the current project (entry project) differs from the host project — meaning the command is being run from a sub-package. When running directly from the monorepo root, the module does nothing.

## Environment Commands

All `poetry env` commands (except `poetry self env`) are intercepted. The module activates the monorepo root virtual environment for the current command. If a virtual environment is already active (detected via `VIRTUAL_ENV` or `CONDA_PREFIX` environment variables), the module skips activation and logs a message in verbose mode.

## Lock, Install, and Update

The `poetry lock`, `poetry install`, and `poetry update` commands are redirected to operate on the monorepo root. The module replaces the command's Poetry instance and installer with ones pointing to the root project, so the shared lockfile and virtual environment are used instead of creating per-package ones.

## Add and Remove

The `poetry add` and `poetry remove` commands are redirected to the monorepo root in the same way as lock and install commands. Dependency changes are applied to the root `pyproject.toml` and lockfile.

# How It Works

The module determines the monorepo root by reading the `host-project` reference from each sub-package's `[tool.ps-plugin]` configuration. The `Environment` model, provided by the SDK, resolves this reference and distinguishes between the entry project (where the command was invoked) and the host project (the monorepo root).

When a command is intercepted, the module creates a new Poetry instance pointing to the host project's `pyproject.toml` and replaces the command's internal Poetry and Installer objects. This redirects all file operations and package resolution to the root without requiring the user to change directories.

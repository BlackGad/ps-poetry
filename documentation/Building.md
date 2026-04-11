# Building the Repository

The workspace uses Poetry with local path dependencies. All packages (plugin, SDK, libraries, modules) are referenced as `develop = true` path dependencies in `pyproject.toml`, so a single `poetry sync` resolves and installs everything.

## Setup

From the workspace root, synchronize the environment:

```bash
poetry sync
```

During this step:

* Poetry resolves all local path dependencies (plugin, SDK, libraries, modules) in develop mode
* The plugin core is installed via `tool.poetry.requires-plugins` from its local path
* The plugin becomes available for all subsequent Poetry commands

## Automated Setup

For a clean environment, use the `setup.ps1` script in the workspace root:

```powershell
.\setup.ps1
```

This script:

1. Removes dot-prefixed folders (except `.agents` and `.vscode`), `__pycache__` directories, and `dist` folders
2. Runs `poetry sync` to restore the workspace environment

## CI Pipeline

The GitHub Actions workflow mirrors the local setup:

1. Installs Poetry via pipx
2. Runs `poetry sync` to set up the environment
3. Runs `poetry check -vvv` to validate packages and execute tests
4. Optionally builds and publishes packages to PyPI

## Requirements

* Poetry 2.3.2 or higher
* Python 3.10 or higher

## Verification

After setup, verify the plugin is correctly installed:

```bash
poetry check
```

The plugin activates during this command, running configured checks across all workspace packages.

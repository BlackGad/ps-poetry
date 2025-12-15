# Building the Repository

The build process for this repository follows a recursive pattern, consisting of two essential steps that must be executed in order.

## Build Process Overview

The build is structured to ensure the plugin core is available before the host project environment is configured. This enables the plugin functionality across the entire monorepo structure.

## Step 1: Build Plugin Core

Navigate to the plugin directory and execute the standard Poetry build command:

```bash
cd plugin
poetry build
```

This generates the plugin wheel file (`.whl`) in the `plugin/dist/` directory. The wheel file follows the naming convention:

```bash
ps_plugin_core-0.0.0-py3-none-any.whl
```

## Step 2: Restore Host Environment

After the plugin core wheel is built, return to the workspace root and synchronize the environment:

```bash
cd ..
poetry sync
```

During this step:

* The host project references the plugin core wheel file via the `tool.poetry.requires-plugins` configuration in `pyproject.toml`
* Poetry installs the plugin from the local wheel file
* The plugin becomes available for the entire repository
* Monorepo mode is activated, enabling plugin functionality across all projects

## Automated Build

For convenience, use the VS Code task "Setup Environment" which executes both steps automatically:

1. Builds the plugin core in the `plugin/` folder
2. Synchronizes the workspace environment

This task is available in the workspace configuration and can be run via the Command Palette (Tasks: Run Task → Setup Environment).

## Build Requirements

* Poetry 2.2.1 or higher
* Python 3.10 or higher
* Active workspace virtual environment

## Verification

After completing the build process, verify the plugin is correctly installed:

```bash
poetry env info
```

The plugin should be listed in the installed packages, and subsequent Poetry commands will have access to the plugin functionality.

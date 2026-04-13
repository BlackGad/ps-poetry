# Overview

[![PyPI](https://img.shields.io/pypi/v/ps-plugin-core)](https://pypi.org/project/ps-plugin-core/)
[![Python](https://img.shields.io/pypi/pyversions/ps-plugin-core)](https://pypi.org/project/ps-plugin-core/)
[![License](https://img.shields.io/pypi/l/ps-plugin-core)](https://pypi.org/project/ps-plugin-core/)

The `ps-plugin-core` package is the core Poetry application plugin. It registers itself as a `poetry.application.plugin` entry point and acts as the host for any number of plugin modules. On activation, the plugin reads the project's `[tool.ps-plugin]` configuration, discovers installed modules via the `ps.module` entry-point group, instantiates them through a built-in [dependency injection](https://github.com/BlackGad/ps-poetry/blob/main/libraries/di/README.md) container, and dispatches lifecycle events to each active module.

For working project examples, see the [ps-poetry-examples](https://github.com/BlackGad/ps-poetry-examples) repository.

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

All installed modules registered under the `ps.module` entry-point group are discovered and loaded. Use the `enabled = false` setting or the `ps disable` command to explicitly opt out.

# Plugin Configuration

All plugin settings reside in the `[tool.ps-plugin]` section of `pyproject.toml`:

* `enabled` (`bool`) — Safety switch to disable the plugin for a project. The plugin activates whenever the `[tool.ps-plugin]` section is present regardless of other settings. Set to `false` to suppress activation.
* `host-project` (`str`) — Relative path to a host project. When set, the plugin reads configuration from that project's `pyproject.toml` and merges it with the current project's settings.
* `modules` (`list[str]`) — Names of plugin modules to activate. Modules are instantiated in the declared order. When omitted, no modules are loaded.

```toml
[tool.ps-plugin]
modules = ["delivery", "check"]
```

## Enable and Disable

The `ps enable` and `ps disable` commands toggle the plugin for the current project by managing the `[tool.ps-plugin]` section in `pyproject.toml`. Both commands are always available, even when the plugin is disabled.

```bash
poetry ps disable
```

Running `ps disable` ensures the `[tool.ps-plugin]` section exists (creating it with an empty `modules` list if absent) and sets `enabled = false`. All module discovery and lifecycle event handling is suppressed until the plugin is re-enabled.

```bash
poetry ps enable
```

Running `ps enable` removes the `enabled = false` entry from `[tool.ps-plugin]`, restoring normal plugin activation. If the plugin is already enabled, the command reports that no changes were necessary.

# Module Loading

Modules are discovered by scanning the `ps.module` entry-point group at runtime. The plugin inspects every loaded object for functions whose names match the pattern `poetry_<event>` or `poetry_<event>_<suffix>`, where `<event>` is one of: `activate`, `command`, `error`, `terminate`, `signal`.

> **Tip:** Entry points cannot be declared for projects with `package-mode = false` because non-package projects are not installed as distributions. To use a project as a plugin module host without publishing it, keep `package-mode = true` and install [`ps-plugin-module-delivery`](https://github.com/BlackGad/ps-poetry/blob/main/modules/delivery/README.md) — then set `deliver = false` in that project's `[tool.ps-plugin]` section to exclude it from delivery operations.

An entry point may resolve to:

* **A class** — instance methods matching the pattern form one module; static/class methods with a suffix form additional modules grouped by suffix.
* **A Python module (namespace)** — all classes and module-level functions inside it are scanned recursively. Functions sharing the same suffix are grouped into a single module.
* **A plain function** — must have a suffix (e.g. `poetry_command_delivery`).

When a Python module contains multiple functions with the same suffix (e.g. `poetry_activate_foo`, `poetry_command_foo`, `poetry_terminate_foo`), they are merged into a single module named by that suffix. This allows a single file to define all lifecycle handlers for one module without requiring a class.

## Module naming

| Source | Name resolution |
| --- | --- |
| Class with `name` attribute | Value of `cls.name` |
| Class without `name` attribute | `cls.__name__` |
| Static/class method or global function | The suffix portion after `poetry_<event>_` |

## Collision detection

When two or more distributions expose a module with the same name, all conflicting modules are skipped and a warning is printed. Non-conflicting modules from all distributions remain available.

When a `modules` list is present in configuration, only those modules are loaded (in the declared order). When the list is absent, no modules are loaded.

# Function Naming Convention

A module class declares its capabilities through method naming. Each function name maps to a specific Poetry console lifecycle event:

* `poetry_activate(application) -> None | bool` — Called once during plugin activation. Returning `False` removes the module from all subsequent event listeners. Any other return value (including `None`) keeps the module active.
* `poetry_command(event) -> None` — Called on every Poetry console command event.
* `poetry_terminate(event) -> None` — Called after a Poetry command finishes.
* `poetry_error(event) -> None` — Called when a Poetry command raises an unhandled error.
* `poetry_signal(event) -> None` — Called on OS signal events during command execution.

A single module class may define any combination of these methods. Optional typing protocols (`PoetryActivateProtocol`, `PoetryCommandProtocol`, etc.) are available in [`ps.plugin.sdk.events`](https://github.com/BlackGad/ps-poetry/blob/main/sdk/README.md) for IDE support but are not required.

# Dependency Injection

Every handler function is invoked through the [`DI.satisfy`](https://github.com/BlackGad/ps-poetry/blob/main/libraries/di/README.md) wrapper, which inspects the function signature and injects registered types as keyword arguments automatically. Constructor parameters of class-based modules are resolved the same way via `DI.spawn`.

The following types are pre-registered by the plugin host and can be used as function/constructor parameters:

| Type | Import | Description |
| --- | --- | --- |
| `IO` | `from cleo.io.io import IO` | Cleo IO for the current Poetry invocation |
| `Application` | `from poetry.console.application import Application` | The active Poetry application instance |
| `Environment` | `from ps.plugin.sdk.project import Environment` | Resolved project [environment](https://github.com/BlackGad/ps-poetry/blob/main/sdk/README.md) with host/workspace access |
| `PluginSettings` | `from ps.plugin.sdk.settings import PluginSettings` | Parsed [`[tool.ps-plugin]` settings](https://github.com/BlackGad/ps-poetry/blob/main/sdk/README.md) |
| `EventDispatcher` | `from cleo.events.event_dispatcher import EventDispatcher` | The Cleo event dispatcher |
| `DI` | `from ps.di import DI` | The dependency injection container itself |

Inside event handlers (`poetry_command`, `poetry_error`, `poetry_terminate`, `poetry_signal`), additional types are registered in a scoped DI container:

| Type | Import | Description |
| --- | --- | --- |
| `ConsoleCommandEvent` | `from cleo.events.console_command_event import ConsoleCommandEvent` | The current command event (for `poetry_command`) |
| `ConsoleTerminateEvent` | `from cleo.events.console_terminate_event import ConsoleTerminateEvent` | The terminate event (for `poetry_terminate`) |
| `ConsoleErrorEvent` | `from cleo.events.console_error_event import ConsoleErrorEvent` | The error event (for `poetry_error`) |
| `ConsoleSignalEvent` | `from cleo.events.console_signal_event import ConsoleSignalEvent` | The signal event (for `poetry_signal`) |

Use [`DI.register`](https://github.com/BlackGad/ps-poetry/blob/main/libraries/di/README.md) to bind additional types from within `poetry_activate` and `DI.resolve` or `DI.resolve_many` to retrieve them in other modules.

# Diagnostics

The plugin writes diagnostic output to the Poetry console at three verbosity levels. Pass `-v`, `-vv`, or `-vvv` to any Poetry command to increase verbosity.

## Standard output (no flags)

No plugin output is produced at the default verbosity level. The plugin activates silently unless an error occurs during module activation, in which case an error message is written to stderr:

```text
[ERROR] Error during activation of module <name>: <reason>
```

## Verbose output (`-v`)

At verbose level the plugin reports its activation lifecycle and any non-fatal discovery warnings. The following lines appear in order:

* `Starting activation` — emitted once when the plugin begins activating.
* `Warning: ps-plugin not enabled or disabled in configuration in <path>` — emitted instead of all subsequent lines when `enabled = false` is set or the `[tool.ps-plugin]` section is absent.
* `Warning: failed to load entry point '<group>:<name>': <reason>` — emitted for each entry point that could not be imported.
* `Warning: entry point '<group>:<name>' loaded unsupported type <type>, skipping.` — emitted when an entry point resolves to an object that is neither a class, module, nor function.
* `Warning: module name collision: '<name>' found in [<dist-a>, <dist-b>]. None will be loaded.` — emitted when two or more distributions expose a module with the same name and different file paths; all conflicting modules are skipped.
* `Selected modules:` — header for the numbered list of modules that will be activated, as specified by the `modules` setting. Each entry shows the module name and its source distribution in brackets.
* `Discovered but not selected:` — header for the list of discovered modules not included in the active set. Each entry shows the module name and its source distribution.
* `Activating <n> module(s)` — emitted before activation handlers are called.
* `Registering <n> handler(s) for <event>` — emitted once per event type (`command`, `terminate`, `error`, `signal`) for which at least one handler was registered.
* `Activation complete` — emitted once when the plugin finishes activating.

## Debug output (`-vvv`)

At debug level all verbose output is included, with the following additions printed in dark gray:

* Full Python traceback following each `failed to load entry point` warning.
* `Module '<name>' discovered via multiple entry points, using single instance` — emitted when the same module file is registered under more than one entry point name; this is treated as a harmless duplicate scan rather than a collision.
* Per-distribution file paths listed under each collision warning entry.
* Source file path for each entry in the `Selected modules` and `Discovered but not selected` lists.
* `Instantiated module <name> (<module>.<class>)` — emitted after each class-based module is instantiated via the DI container.
* `Module <name> handles: <event1>, <event2>` — emitted for each module listing its registered event types.
* `No handlers for <event>; skipping listener` — emitted for event types that have no registered handlers.
* `Executing activate for module <name>` — emitted before each module's `poetry_activate` handler is called.
* `Module <name> disabled itself during activation` — emitted when `poetry_activate` returns `False`.
* `Processing <event> event` — emitted each time an event listener fires during command execution.
* `Command execution stopped after <event> handler` — emitted when a `command` handler cancels command execution.

# Advanced: Creating Your Own Module

This section guides you through creating and publishing your own plugin module. A plugin module can extend existing Poetry commands, add new commands, or hook into the Poetry execution lifecycle.

## Module Structure

A plugin module is a Python package with an entry point registered under the `ps.module` group. The simplest structure:

```bash
my-custom-module/
├── pyproject.toml
├── README.md
├── main.py          # Your package code
└── ps-extension.py  # Plugin module (separate file)
```

## Step 1: Create the Project

Create a new Poetry project:

```bash
mkdir my-custom-module
cd my-custom-module
poetry init -n
```

Configure your `pyproject.toml` to register the module entry point and require the plugin:

```toml
# Register your extension module entry point
[project.entry-points."ps.module"]
my_module = "ps-extension"  # Points to ps-extension.py file

# Define what gets packaged and distributed
[tool.poetry]
packages = [
    { include = "main.py" }  # Only package main.py, NOT ps-extension.py
]

# Require ps-plugin-core to be installed as a Poetry plugin
[tool.poetry.requires-plugins]
ps-plugin-core = "*"

# Enable the plugin and activate your module
[tool.ps-plugin]
modules = ["foo"]  # Module name from the entry point above

## Step 2: Implement the Module

Create `main.py` with your package code:

```python
def hello():
    print("Hello World!")
```

Create `ps-extension.py` with the plugin activation function:

```python
def poetry_activate_foo(application):
    print("Hello from extension!")
```

The `poetry_activate` function is called once when the plugin activates. The `application` parameter is automatically injected by the dependency injection system.

> **Note:** For the simplest extension, you don't need `ps-plugin-sdk`. Add it only when you need access to SDK utilities like `Environment`, `PluginSettings`, or helper functions.

### Advanced: Use a Module Class

For more complex modules that need to maintain state or handle multiple events, use a class.

First, add `ps-plugin-sdk` to your dependencies:

```bash
poetry add ps-plugin-sdk
```

Then implement your module class:

```python
from typing import ClassVar

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.io.inputs.option import Option
from poetry.console.application import Application
from poetry.console.commands.check import CheckCommand

from ps.plugin.sdk.events import ensure_option


class MyModule:
    name: ClassVar[str] = "my-module"

    def poetry_activate(self, application: Application) -> bool:
        ensure_option(CheckCommand, Option(
            name="strict",
            description="Enable strict validation mode.",
            shortcut="s",
            flag=True
        ))
        return True

    def poetry_command(self, event: ConsoleCommandEvent) -> None:
        if not isinstance(event.command, CheckCommand):
            return

        io = event.io
        strict_mode = io.input.options.get("strict", False)

        if strict_mode:
            io.write_line("<info>Running in strict mode</info>")
            # Add your strict validation logic here
```

### Advanced: Add a Custom Command

This example adds a new `poetry status` command to display workspace information:

```python
from typing import ClassVar

from cleo.commands.command import Command
from cleo.io.inputs.option import Option
from poetry.console.application import Application

from ps.di import DI
from ps.plugin.sdk.project import Environment


class StatusCommand(Command):
    name = "status"
    description = "Display workspace status and project information."
    options = [
        Option("--verbose", "-v", flag=True, description="Show detailed information")
    ]

    def __init__(self, di: DI) -> None:
        super().__init__()
        self._di = di

    def handle(self) -> int:
        environment = self._di.resolve(Environment)
        assert environment is not None

        io = self.io
        verbose = self.option("verbose")

        io.write_line(f"<info>Host project:</info> {environment.host_project.name.value}")
        io.write_line(f"<info>Total projects:</info> {len(environment.projects)}")

        if verbose:
            io.write_line("\n<info>Projects:</info>")
            for project in environment.projects:
                io.write_line(f"  - {project.name.value} ({project.path})")

        return 0


class MyModule:
    name: ClassVar[str] = "my-module"

    def poetry_activate(self, application: Application, di: DI) -> bool:
        application.add(di.spawn(StatusCommand))
        return True
```

## Step 3: Use Dependency Injection

All handler functions and command constructors are invoked through the [`DI.satisfy`](https://github.com/BlackGad/ps-poetry/blob/main/libraries/di/README.md) wrapper. Simply declare parameters with type hints and they will be injected automatically.

### Pre-registered Types

The following types are available for injection in any handler:

* `Application` (from `poetry.console.application`) — The Poetry application instance
* `IO` (from `cleo.io.io`) — Console input/output interface
* `Environment` (from `ps.plugin.sdk.project`) — Workspace environment with all discovered projects
* `PluginSettings` (from `ps.plugin.sdk.settings`) — Parsed `[tool.ps-plugin]` configuration
* `EventDispatcher` (from `cleo.events.event_dispatcher`) — Cleo event dispatcher
* `DI` (from `ps.di`) — The dependency injection container itself

Inside event handlers, these additional types are available:

* `ConsoleCommandEvent` (from `cleo.events.console_command_event`)
* `ConsoleTerminateEvent` (from `cleo.events.console_terminate_event`)
* `ConsoleErrorEvent` (from `cleo.events.console_error_event`)
* `ConsoleSignalEvent` (from `cleo.events.console_signal_event`)

### Register Custom Types

Register your own types in `poetry_activate`:

```python
from ps.di import DI
from my_namespace.services import MyService


class MyModule:
    name: ClassVar[str] = "my-module"

    def poetry_activate(self, di: DI) -> bool:
        di.register(MyService).singleton()
        return True

    def poetry_command(self, service: MyService) -> None:
        service.do_something()
```

## Step 4: Test Locally

Plugin modules must be installed as packages — they cannot be defined inline within a project. Create a separate test project and install your module as a path dependency:

```bash
mkdir test-project
cd test-project
poetry init -n
```

Add your module as a development dependency in the test project's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.10"
my-custom-module = { path = "../my-custom-module", develop = true }

[tool.ps-plugin]
modules = ["my-module"]
```

Install dependencies and test your module:

```bash
poetry install
poetry check -v
# or
poetry status -v
```

> **Note:** Entry points require `package-mode = true` (the default). Projects with `package-mode = false` are not installed as distributions and cannot expose entry points. Always keep your module project in package mode.

## Step 5: Publish Your Module

Build and publish your module to PyPI:

```bash
poetry build
poetry publish
```

Users can then install it globally or per-project:

```bash
poetry self add my-custom-module
```

Or declare it in `pyproject.toml`:

```toml
[tool.poetry.requires-plugins]
my-custom-module = "*"

[tool.ps-plugin]
modules = ["my-module"]
```

## Module Best Practices

* **Unique naming** — Use a distinctive module name to avoid collisions. Include a prefix or namespace (e.g., `company-module-name`).
* **Minimal activation** — Return `False` from `poetry_activate` when your module should not participate (e.g., when required configuration is missing).
* **Event filtering** — In `poetry_command`, check `isinstance(event.command, TargetCommand)` before processing to avoid interfering with unrelated commands.
* **Disable with care** — Call `event.disable_command()` only when you fully replace the original command's behavior. Otherwise, let it execute normally.
* **Respect verbosity** — Print informational output only when `io.is_verbose()` or `io.is_debug()` returns `True`.
* **Type hints** — Always provide type hints on function parameters to enable automatic dependency injection.
* **Documentation** — Document your module's configuration options, commands, and expected behavior in a README.

## Complete Example

For complete working examples, see:

* [ps-plugin-module-check](https://github.com/BlackGad/ps-poetry/blob/main/modules/check/README.md) — Extends the `poetry check` command with configurable quality checks
* [ps-plugin-module-delivery](https://github.com/BlackGad/ps-poetry/blob/main/modules/delivery/README.md) — Adds a `poetry delivery` command and extends `poetry build` and `poetry publish`
* [ps-poetry-examples](https://github.com/BlackGad/ps-poetry-examples) — Working project examples demonstrating module usage

## Troubleshooting

**Module not loaded:** Ensure `[project.entry-points."ps.module"]` is declared correctly and points to a valid Python module or class. Run `poetry install` after modifying entry points.

**Dependencies not injected:** Verify that all function parameters have type hints matching registered types. Check that `ps.di` is imported from `ps.di`, not `ps.dependency_injection`.

**Name collision:** If another distribution exposes a module with the same name, both modules will be skipped. Choose a unique name or configure your module as the only one in the `modules` list.

# Extension Scaffolding

The `ps setup-extension` command provides interactive scaffolding for creating new plugin modules directly inside the current project. It generates the extension source file, registers the entry point in `pyproject.toml`, and adds the module to the `[tool.ps-plugin] modules` list.

Run the command from a project directory:

```bash
poetry ps setup-extension
```

The command prompts for an extension name, a template, and any template-specific questions. It then writes the generated file into an `extensions/` directory relative to the project root and updates `pyproject.toml` accordingly.

The generated entry point value follows the pattern `extensions.<snake_name>`, where `<snake_name>` is the normalized module name (lowercased with hyphens and dots replaced by underscores).

Four default variables are available in every template:

* `{name}` — the original extension name as entered by the user
* `{safe_name}` — name with hyphens and dots replaced by underscores, preserving case
* `{snake_name}` — lowercase version of `safe_name`
* `{pascal_name}` — PascalCase version of the name

## Built-in Templates

Three templates are included out of the box.

### Entry functions

Function-based extension module with all poetry handler functions. Each function follows the `poetry_<event>_<suffix>` naming convention and receives the appropriate event type. Functions sharing the same suffix are automatically grouped into a single module during discovery.

```python
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from poetry.console.application import Application


def poetry_activate_my_ext(application: Application) -> bool:
    print("Hello from extension my_ext")
    return True


def poetry_command_my_ext(event: ConsoleCommandEvent) -> None:
    print("Command event in my_ext")


def poetry_terminate_my_ext(event: ConsoleTerminateEvent) -> None:
    print("Terminate event in my_ext")
```

### Entry class

Class-based extension module where all handler methods belong to a single `ExtensionModule` class. The class `name` attribute determines the module name. Instance methods do not require a suffix.

```python
from typing import ClassVar

from cleo.events.console_command_event import ConsoleCommandEvent
from poetry.console.application import Application


class ExtensionModule:
    name: ClassVar[str] = "my-ext"

    def poetry_activate(self, application: Application) -> bool:
        print("Hello from extension my-ext")
        return True

    def poetry_command(self, event: ConsoleCommandEvent) -> None:
        print("Command event in my-ext")
```

### Custom command

Module that registers a new Poetry command. The template prompts for a command name and generates a `CustomCommand` class with example arguments and options, along with an activation function that registers it with the application.

```python
from cleo.commands.command import Command
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from poetry.console.application import Application


class CustomCommand(Command):
    name = "greet"
    description = ""
    arguments = [
        Argument(name="arg-value", description="A single argument value", default=None, required=False),
    ]
    options = [
        Option("--flag", flag=True, requires_value=False, shortcut="j", description="Flag option"),
    ]

    def handle(self) -> int:
        print("Handling greet")
        return 0


def poetry_activate_my_ext(application: Application) -> bool:
    application.add(CustomCommand())
    return True
```

## Custom Templates

Additional templates can be provided by any installed package through the dependency injection system. Register an `ExtensionTemplate` implementation from `ps.plugin.sdk.setup_extension_template` in the DI container during plugin activation, and it will appear in the template selection list alongside the built-in templates.

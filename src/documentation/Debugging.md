# Debugging the Plugin

For convenient plugin development and testing, the workspace provides a debugging configuration that allows you to inject and test the plugin in any target project.

## Launch Configuration

The workspace includes a pre-configured launch profile called **"Launch Poetry with debugpy"** that enables plugin debugging with full debugger support.

## How to Use

1. Open the Run and Debug panel in VS Code (Ctrl+Shift+D)
2. Select **"Launch Poetry with debugpy"** from the dropdown
3. Click the Start Debugging button (F5)
4. When prompted, provide:
   - **Target project path**: Absolute or relative path to the project where the plugin should be tested
   - **Poetry command**: The Poetry command to execute (e.g., `install`, `update`, `env info`)

## How It Works

The debugging process performs the following steps:

1. Executes the **Debugging** task that prepares the environment
2. Launches [launcher.py](../launcher.py) with the debugpy debugger attached
3. Patches Poetry's Application class to inject the plugin
4. Runs Poetry with the specified command in the target project context
5. Plugin activation occurs with full debugger support enabled

## Plugin Injection Mechanism

The launcher performs the following operations:

- Adds the plugin source to Python's module search path
- Patches Poetry's `Application.__init__` method to inject the plugin
- Activates the plugin before Poetry command execution
- Runs Poetry with `--no-plugins` flag to prevent double activation from installed plugins

## Debugging Features

During debugging sessions, you can:

- Set breakpoints in plugin source code (`plugin/src/ps/plugin/core/`)
- Step through plugin activation and event handling
- Inspect Poetry's internal state and objects
- Monitor plugin behavior in real-time
- Test plugin functionality in isolated project environments

## Example Workflow

To debug the plugin when running `poetry install` in a test project:

1. Start debugging (F5)
2. Enter target path: `C:\path\to\test\project`
3. Enter command: `install`
4. Set breakpoints in your plugin code
5. Step through execution as Poetry runs

## Configuration Files

The debugging configuration is defined in:

- **Launch profile**: [workspace.code-workspace](../workspace.code-workspace) under `launch.configurations`
- **Debug task**: [workspace.code-workspace](../workspace.code-workspace) under `tasks`
- **Launcher script**: [launcher.py](../launcher.py)
- **Environment variables**: [debug.env](../debug.env) (automatically generated during Debugging task execution)

## Requirements

- VS Code with Python and Debugpy extensions installed
- Active workspace virtual environment
- Built plugin core (see [Building.md](Building.md))

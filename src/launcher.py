import os
import sys
import runpy
from pathlib import Path

from plugin.src.ps.plugin.core.plugin import Plugin
from poetry.console.application import Application as PoetryApplication

LOG_PREFIX = "[PS-Plugin]"


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}")


def main() -> None:
    log("Initializing Poetry launcher...")

    workspace_root = Path(__file__).parent
    target_project = Path(os.environ.get("DEBUG_PROJECT_PATH", Path.cwd()))
    command_line = os.environ.get("DEBUG_COMMAND_LINE")

    log(f"Target: {target_project.resolve()}")
    log(f"Command: {command_line if command_line else '<none>'}'")

    # Add plugin source to Python path
    plugin_src_path = workspace_root / "plugin" / "src"
    if str(plugin_src_path) not in sys.path:
        sys.path.insert(0, str(plugin_src_path))
        log(f"Plugin path: {plugin_src_path}")

    # Activate target virtual environment if present
    venv_path = target_project / ".venv"
    if venv_path.exists():
        os.environ["VIRTUAL_ENV"] = str(venv_path)
        site_packages = venv_path / ("Lib" if os.name == "nt" else "lib") / "site-packages"

        if site_packages.exists():
            sys.path.insert(0, str(site_packages))
            log(f"Virtual environment: {venv_path}")
        else:
            log("Warning: Virtual environment found but missing site-packages")
    else:
        log("No virtual environment found")

    os.chdir(target_project)

    # Patch Poetry Application to inject plugin
    original_init = PoetryApplication.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        try:
            Plugin().activate(self)
            log("Plugin activated successfully")
        except Exception as error:
            log(f"Error: Plugin activation failed - {error}")

    PoetryApplication.__init__ = patched_init  # type: ignore[method-assign]

    # Prepare Poetry command arguments
    sys.argv = ["poetry", *command_line.split()] if command_line else ["poetry"]

    # Disable auto-loading of installed plugins
    if "--no-plugins" not in sys.argv:
        sys.argv.insert(1, "--no-plugins")

    log(f"Running: {' '.join(sys.argv)}")
    runpy.run_module("poetry", run_name="__main__")


if __name__ == "__main__":
    main()

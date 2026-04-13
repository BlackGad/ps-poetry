from typing import Any

import tomlkit
from cleo.commands.command import Command
from poetry.console.application import Application


class EnableCommand(Command):
    name = "ps enable"
    description = "Enable the ps-plugin for the current project."

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application

    def handle(self) -> int:
        pyproject = self._application.poetry.pyproject  # type: ignore[attr-defined]
        document = pyproject.data

        ps_plugin = _ensure_ps_plugin_section(document)

        if "enabled" in ps_plugin and not bool(ps_plugin["enabled"]):
            del ps_plugin["enabled"]
            self.line("<info>Removed 'enabled = false' from [tool.ps-plugin].</info>")
        else:
            self.line("<comment>Plugin is already enabled.</comment>")

        pyproject.save()
        return 0


class DisableCommand(Command):
    name = "ps disable"
    description = "Disable the ps-plugin for the current project."

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application

    def handle(self) -> int:
        pyproject = self._application.poetry.pyproject  # type: ignore[attr-defined]
        document = pyproject.data

        ps_plugin = _ensure_ps_plugin_section(document)

        if "enabled" in ps_plugin and not bool(ps_plugin["enabled"]):
            self.line("<comment>Plugin is already disabled.</comment>")
        else:
            ps_plugin["enabled"] = False
            self.line("<info>Set 'enabled = false' in [tool.ps-plugin].</info>")

        pyproject.save()
        return 0


def _ensure_ps_plugin_section(document: tomlkit.TOMLDocument) -> Any:
    if "tool" not in document:
        document["tool"] = tomlkit.table()
    tool: Any = document["tool"]

    if "ps-plugin" not in tool:
        tool["ps-plugin"] = tomlkit.table()
        tool["ps-plugin"]["modules"] = tomlkit.array()

    return tool["ps-plugin"]

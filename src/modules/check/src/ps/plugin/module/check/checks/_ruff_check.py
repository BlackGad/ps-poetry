from pathlib import Path
from typing import ClassVar

from ._tool_check import ToolCheck


class RuffCheck(ToolCheck):
    name: ClassVar[str] = "ruff"

    def _build_command(self, source_paths: list[Path], fix: bool) -> list[str]:
        command = ["ruff", "check"]
        if fix:
            command.append("--fix")
        command.extend([str(path) for path in source_paths])
        return command

from pathlib import Path
from typing import ClassVar

from ._tool_check import ToolCheck


class PylintCheck(ToolCheck):
    name: ClassVar[str] = "pylint"

    def _build_command(self, source_paths: list[Path], fix: bool) -> list[str]:
        command = ["pylint"]
        command.extend([str(path) for path in source_paths])
        return command

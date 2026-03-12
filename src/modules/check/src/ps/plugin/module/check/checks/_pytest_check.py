from pathlib import Path
from typing import ClassVar

from ._tool_check import ToolCheck


class PytestCheck(ToolCheck):
    name: ClassVar[str] = "pytest"

    def _build_command(self, source_paths: list[Path], fix: bool) -> list[str]:
        command = ["pytest"]
        command.extend([str(path) for path in source_paths])
        return command

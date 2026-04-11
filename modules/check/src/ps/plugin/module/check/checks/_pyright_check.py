from pathlib import Path
from typing import ClassVar

from ._tool_check import ToolCheck


class PyrightCheck(ToolCheck):
    name: ClassVar[str] = "pyright"

    def _build_command(self, source_paths: list[Path], fix: bool) -> list[str]:
        command = ["pyright"]
        command.extend([str(path) for path in source_paths])
        return command

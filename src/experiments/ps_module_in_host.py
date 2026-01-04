from cleo.io.io import IO
from poetry.console.application import Application


class ModuleInHost:
    def __init__(self, io: IO) -> None:
        self._io = io

    def handle_activate(self, application: Application) -> bool:
        self._io.write_line("Module in host global setup executed")
        return True

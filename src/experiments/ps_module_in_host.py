from cleo.io.io import IO


class ModuleInHost:
    def __init__(self, io: IO) -> None:
        self._io = io

    def poetry_activate(self) -> bool:
        self._io.write_line("Module in host global setup executed")
        return True

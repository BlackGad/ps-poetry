from cleo.io.io import IO
from poetry.console.application import Application


class ModuleInHost:
    def __init__(self, io: IO) -> None:
        self._io = io

    def global_setup(self, application: Application) -> None:
        self._io.write_line("Module in host global setup executed")

    @staticmethod
    def get_module_name() -> str:
        return "Test module in host"

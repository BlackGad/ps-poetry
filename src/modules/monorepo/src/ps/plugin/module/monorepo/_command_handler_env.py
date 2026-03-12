import os

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from poetry.console.commands.env_command import EnvCommand
from poetry.console.commands.installer_command import InstallerCommand
from poetry.console.commands.self.self_command import SelfCommand
from poetry.installation.installer import Installer
from poetry.utils.env import EnvManager

from ps.plugin.sdk.project import Environment

from ._command_handler_protocol import CommandHandlerProtocol
from ._monorepo_root import _create_root_poetry


class EnvCommandHandler(CommandHandlerProtocol):
    @staticmethod
    def can_handle(event: ConsoleCommandEvent, environment: Environment) -> bool:
        if not isinstance(event.command, EnvCommand) or isinstance(event.command, SelfCommand):
            return False
        return environment.host_project != environment.entry_project

    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    def handle_command(self, event: ConsoleCommandEvent) -> None:
        io = event.io
        command = event.command
        assert isinstance(command, EnvCommand)

        env_prefix = os.environ.get("VIRTUAL_ENV", os.environ.get("CONDA_PREFIX"))
        conda_env_name = os.environ.get("CONDA_DEFAULT_ENV")
        in_venv = env_prefix is not None and conda_env_name != "base"
        if in_venv:
            if io.is_verbose():
                io.write_line(f"Detected existing virtual environment (<comment>{env_prefix}</comment>), skipping monorepo root venv activation.")
            return

        monorepo_root_poetry = _create_root_poetry(self._environment, command.poetry.disable_cache, io)
        env_manager = EnvManager(monorepo_root_poetry, io=io)
        root_env = env_manager.create_venv()
        command.set_env(root_env)

        if not isinstance(command, InstallerCommand):
            return

        installer = Installer(
            io,
            root_env,
            command.poetry.package,
            command.poetry.locker,
            command.poetry.pool,
            command.poetry.config,
            disable_cache=command.poetry.disable_cache,
        )
        command.set_installer(installer)

        if io.is_verbose():
            io.write_line(f"Activated monorepo root virtual environment at <comment>{root_env.path}</comment>")

    def handle_terminate(self, event: ConsoleTerminateEvent) -> None:
        pass

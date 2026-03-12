from cleo.io.io import IO
from poetry.config.config import Config
from poetry.console.commands.installer_command import InstallerCommand
from poetry.factory import Factory
from poetry.installation.installer import Installer
from poetry.poetry import Poetry

from ps.plugin.sdk.project import Environment


def _create_root_poetry(environment: Environment, disable_cache: bool, io: IO) -> Poetry:
    Config.create(reload=True)
    monorepo_root = environment.host_project.path
    return Factory().create_poetry(cwd=monorepo_root, io=io, disable_cache=disable_cache)


def _redirect_to_monorepo_root(command: InstallerCommand, environment: Environment, io: IO) -> None:
    monorepo_root_poetry = _create_root_poetry(environment, command.poetry.disable_cache, io)
    installer = Installer(
        io,
        command.env,
        monorepo_root_poetry.package,
        monorepo_root_poetry.locker,
        monorepo_root_poetry.pool,
        monorepo_root_poetry.config,
        disable_cache=monorepo_root_poetry.disable_cache,
    )
    command.set_poetry(monorepo_root_poetry)
    command.set_installer(installer)

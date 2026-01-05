"""
Copyright (C) 2024 GlaxoSmithKline plc

Licensed under the Apache License, Version 2.0 (the "License");
"""
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent

from poetry.factory import Factory
from poetry.config.config import Config
from poetry.console.commands.install import InstallCommand
from poetry.console.commands.lock import LockCommand
from poetry.console.commands.update import UpdateCommand
from poetry.installation.installer import Installer

from ps.plugin.sdk import Environment

from .command_handler_protocol import CommandHandlerProtocol


class LockCommandHandler(CommandHandlerProtocol):
    @staticmethod
    def can_handle(event: ConsoleCommandEvent, environment: Environment) -> bool:
        # Handle only 'env' commands that are 'lock', 'install' or 'update' commands
        if not isinstance(event.command, (LockCommand, InstallCommand, UpdateCommand)):
            return False
        # Handle only if host project is different from entry project
        return environment.host_project != environment.entry_project

    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    def handle_command(self, event: ConsoleCommandEvent) -> None:
        io = event.io
        command = event.command
        assert isinstance(command, (LockCommand, InstallCommand, UpdateCommand))
        poetry = command.poetry

        # Force reload global config in order to undo changes that happened due to subproject's poetry.toml configs
        _ = Config.create(reload=True)
        monorepo_root = self._environment.host_project.path
        monorepo_root_poetry = Factory().create_poetry(
            cwd=monorepo_root,
            io=io,
            disable_cache=poetry.disable_cache
        )

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

    def handle_terminate(self, event: ConsoleTerminateEvent) -> None:
        pass

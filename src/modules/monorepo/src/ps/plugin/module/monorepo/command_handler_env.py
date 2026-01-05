"""
Copyright (C) 2024 GlaxoSmithKline plc

Licensed under the Apache License, Version 2.0 (the "License");
"""

import os

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent

from poetry.factory import Factory
from poetry.config.config import Config
from poetry.utils.env import EnvManager
from poetry.console.commands.env_command import EnvCommand
from poetry.console.commands.self.self_command import SelfCommand
from poetry.console.commands.installer_command import InstallerCommand
from poetry.installation.installer import Installer

from ps.plugin.sdk import Environment

from .command_handler_protocol import CommandHandlerProtocol


class EnvCommandHandler(CommandHandlerProtocol):
    @staticmethod
    def can_handle(event: ConsoleCommandEvent, environment: Environment) -> bool:
        # Handle only 'env' commands that are not 'self' commands
        if not isinstance(event.command, EnvCommand) or isinstance(event.command, SelfCommand):
            return False
        # Handle only if host project is different from entry project
        return environment.host_project != environment.entry_project

    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    def handle_command(self, event: ConsoleCommandEvent) -> None:
        io = event.io
        command = event.command
        assert isinstance(command, EnvCommand)

        poetry = command.poetry

        # We don't want to activate the monorepo root venv if we are already inside a venv
        # in order to be consistent with poetry's current behavior.
        # Check if we are inside a virtualenv or not
        # Conda sets CONDA_PREFIX in its envs, see
        # https://github.com/conda/conda/issues/2764
        env_prefix = os.environ.get("VIRTUAL_ENV", os.environ.get("CONDA_PREFIX"))
        conda_env_name = os.environ.get("CONDA_DEFAULT_ENV")
        # It's probably not a good idea to pollute Conda's global "base" env, since
        # most users have it activated all the time.
        in_venv = env_prefix is not None and conda_env_name != "base"
        if in_venv:
            if io.is_verbose():
                io.write_line(f"Detected existing virtual environment (<comment>{env_prefix}</comment>), skipping monorepo root venv activation.")
            return

        # Force reload global config in order to undo changes that happened due to subproject's poetry.toml configs
        _ = Config.create(reload=True)
        monorepo_root = self._environment.host_project.path
        monorepo_root_poetry = Factory().create_poetry(
            cwd=monorepo_root,
            io=io,
            disable_cache=poetry.disable_cache)

        env_manager = EnvManager(monorepo_root_poetry, io=io)
        root_env = env_manager.create_venv()
        command.set_env(root_env)

        if not isinstance(command, InstallerCommand):
            return

        # Update installer for commands that require an installer
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

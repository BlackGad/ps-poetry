from typing import ClassVar, Optional, Type

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.input import Input
from cleo.io.inputs.option import Option
from cleo.io.io import IO
from poetry.console.application import Application
from poetry.console.commands.check import CheckCommand

from ps.di import DI
from ps.plugin.module.check._check import ICheck
from ps.plugin.sdk.events import ensure_argument, ensure_option
from ps.plugin.sdk.mixins import NameAwareProtocol
from ps.plugin.sdk.project import Environment, Project, filter_projects

from ._check_settings import CheckSettings
from .checks import (
    EnvironmentCheck,
    ImportsCheck,
    PoetryCheck,
    PylintCheck,
    PyrightCheck,
    PytestCheck,
    RuffCheck,
)


def _filter_checkers[T: NameAwareProtocol](available_checkers: list[T], check_settings: CheckSettings, io: IO) -> list[T]:
    # Explicitly specified checks in settings
    specified_checks = check_settings.checks if check_settings.checks is not None else []

    # Get specified checkers in order
    specified_checkers = sorted(
        [checker for checker in available_checkers if checker.name in specified_checks],
        key=lambda c: specified_checks.index(c.name)
    )

    # Get available but not specified checkers
    available_not_specified = [
        checker for checker in available_checkers if checker.name not in specified_checks
    ]

    # Print selected checkers only in verbose mode
    if io.is_verbose():
        io.write_line("<fg=magenta>Selected checkers:</> ")
        for idx, checker in enumerate(specified_checkers, start=1):
            io.write_line(f"  {idx}. <fg=cyan>{checker.name}</>")

    # Print available but not selected checkers in verbose mode
    if io.is_verbose() and available_not_specified:
        io.write_line("\n<fg=magenta>Available but not selected:</> ")
        for checker in available_not_specified:
            io.write_line(f"  - <fg=dark_gray>{checker.name}</>")

    return specified_checkers


def _get_inputs(input: Input) -> list[str]:
    return input.arguments.get("inputs", [])


def _get_fix_option(input: Input) -> bool:
    return input.options.get("fix", False)


def _get_continue_on_error_option(input: Input) -> bool:
    return input.options.get("continue-on-error", False)


def _perform_checks(di: DI, projects: list[Project], checkers: list[ICheck], fix: bool, continue_on_error: bool) -> int:
    if not checkers:
        return 0
    io = di.resolve(IO)
    assert io is not None
    result = 0
    for checker in checkers:
        io.write_line(f"<fg=cyan>{checker.name.upper()}</>")
        if not checker.can_check(projects):
            if io.is_debug():
                io.write_line("<fg=yellow>Skipping checker as it cannot check the provided projects in current environment.</>")
            continue
        exception = checker.check(io, projects, fix)
        if exception is not None:
            io.write_line(f"<error>{exception}</error>")
            result = 1
            if not continue_on_error:
                return result
    return result


_builtin_checks: list[Type[ICheck]] = [
    PoetryCheck,
    EnvironmentCheck,
    ImportsCheck,
    PytestCheck,
    PylintCheck,
    RuffCheck,
    PyrightCheck,
]


class CheckModule:
    name: ClassVar[str] = "ps-check"

    def __init__(self, di: DI) -> None:
        for check_cls in _builtin_checks:
            di.register(ICheck).implementation(check_cls)
        self._di = di
        self._exit_code: Optional[int] = None

    def poetry_activate(self, application: Application) -> bool:
        ensure_argument(CheckCommand, Argument(
            name="inputs",
            description="Optional inputs pointers to check. It could be project names or paths. If not provided, all discovered projects will be checked.",
            is_list=True,
            required=False)
        )
        ensure_option(CheckCommand, Option(
            name="fix",
            description="Instruct to perform automatic issues fix where possible.",
            shortcut="f",
            flag=True)
        )
        ensure_option(CheckCommand, Option(
            name="continue-on-error",
            description="Continue checking even after a check failure.",
            shortcut="c",
            flag=True)
        )
        return True

    def poetry_command(self, event: ConsoleCommandEvent) -> None:
        if not isinstance(event.command, CheckCommand):
            return
        event.disable_command()

        environment = self._di.resolve(Environment)
        assert environment is not None

        inputs = _get_inputs(event.io.input)
        if not inputs and environment.host_project != environment.entry_project:
            inputs.append(str(environment.entry_project.path))

        filtered_projects = filter_projects(inputs, environment.projects)
        if not filtered_projects:
            event.io.write_line("<comment>No projects found to process.</comment>")
            return

        fix = _get_fix_option(event.io.input)
        continue_on_error = _get_continue_on_error_option(event.io.input)

        plugin_settings = environment.host_project.plugin_settings
        check_settings = CheckSettings.model_validate(plugin_settings.model_dump(), by_alias=True)

        available_checkers = self._di.resolve_many(ICheck)
        checkers = _filter_checkers(available_checkers, check_settings, event.io)

        if not checkers:
            event.io.write_line("<comment>No checkers selected to run.</comment>")
            return

        if fix:
            event.io.write_line("<fg=green>Automatic fix enabled</>")
        if continue_on_error:
            event.io.write_line("<fg=magenta>Continue on error enabled</>")
        event.io.write_line(f"\n<fg=magenta>Checking <comment>{len(filtered_projects)}</comment> project(s)</>")
        self._exit_code = _perform_checks(self._di, filtered_projects, checkers, fix, continue_on_error)

    def poetry_terminate(self, event: ConsoleTerminateEvent) -> None:
        if self._exit_code is not None:
            event.set_exit_code(self._exit_code)

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from typing import ClassVar, Optional, Type

from cleo.io.io import IO
from cleo.io.inputs.input import Input
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from poetry.console.commands.check import CheckCommand
from poetry.console.application import Application


from ps.plugin.sdk import (
    Project,
    Environment,
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    NameAwareProtocol,
    DI,
    ICheck,
    ensure_argument,
    ensure_option,
    filter_projects,
)

from .check_settings import CheckSettings
from .checks.poetry_check import PoetryCheck
from .checks.environment_check import EnvironmentCheck
from .checks.ruff_check import RuffCheck
from .checks.pylint_check import PylintCheck
from .checks.pytest_check import PytestCheck


def _filter_checkers[T: NameAwareProtocol](available_checkers: list[T], check_settings: CheckSettings, io: IO, checker_type: str) -> list[T]:
    if check_settings.checks_include is not None:
        checks_include = check_settings.checks_include
        include_checkers = sorted(
            [checker for checker in available_checkers if checker.name in checks_include],
            key=lambda c: checks_include.index(c.name)
        )
    else:
        include_checkers = list(available_checkers)
    exclude_checkers = (
        [checker for checker in available_checkers if checker.name in check_settings.checks_exclude]
        if check_settings.checks_exclude is not None
        else []
    )
    io.write_line(f"<fg=magenta>{checker_type} checkers:</>")
    if not available_checkers:
        io.write_line(f"  <comment>No {checker_type.lower()} checkers available.</comment>")
        return []
    for checker in available_checkers:
        status = "<fg=dark_gray>not included</>"
        if checker in include_checkers:
            status = "<fg=light_green>included</>"
        if checker in exclude_checkers:
            status = "<fg=light_red>excluded</>"
        io.write_line(f"  - <fg=cyan>{checker.name}</>: {status}")
    return [checker for checker in include_checkers if checker not in exclude_checkers]


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
    PytestCheck,
    PylintCheck,
    RuffCheck,
]


class CheckModule(
    NameAwareProtocol,
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol
):
    name: ClassVar[str] = "ps-check"

    def __init__(self, di: DI) -> None:
        for check_cls in _builtin_checks:
            di.register(ICheck).implementation(check_cls)
        self._di = di
        self._exit_code: Optional[int] = None

    def handle_activate(self, application: Application) -> bool:
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

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
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
        checkers = _filter_checkers(available_checkers, check_settings, event.io, "Checks")

        if fix:
            event.io.write_line("<fg=magenta>Automatic fix enabled</>")
        if continue_on_error:
            event.io.write_line("<fg=magenta>Continue on error enabled</>")
        event.io.write_line(f"<info>Checking <comment>{len(filtered_projects)}</comment> project(s)</info>")
        self._exit_code = _perform_checks(self._di, filtered_projects, checkers, fix, continue_on_error)

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if self._exit_code is not None:
            event.set_exit_code(self._exit_code)

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event_dispatcher import EventDispatcher
from typing import ClassVar

from cleo.io.io import IO
from cleo.io.buffered_io import BufferedIO
from cleo.io.inputs.input import Input
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from poetry.console.commands.check import CheckCommand
from poetry.console.application import Application


from ps.plugin.module.check.check_settings import CheckSettings
from ps.plugin.sdk.models import Project, Environment
from ps.plugin.sdk.protocols import (
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    NameAwareProtocol,
)
from ps.plugin.sdk.interfaces import DI
from ps.plugin.sdk.helpers import ensure_argument, ensure_option, filter_projects

from .sdk import IProjectCheck, ISolutionCheck

from .checks.project_poetry import ProjectPoetryCheck
from .checks.solution_ruff import SolutionRuffCheck


def _filter_checkers[T: NameAwareProtocol](available_checkers: list[T], check_settings: CheckSettings, io: IO, checker_type: str) -> list[T]:
    include_checkers = (
        [checker for checker in available_checkers if checker.name in check_settings.checks_include]
        if check_settings.checks_include is not None
        else available_checkers
    )
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


def _perform_project_check(di: DI, project: Project, project_checkers: list[IProjectCheck], fix: bool) -> int:
    io = di.resolve(IO)
    assert io is not None
    io.write_line(f" - <comment>{project.defined_name or "unknown"}</comment>")
    if not project_checkers:
        return 0

    for checker in project_checkers:
        if not checker.can_check(project):
            if io.is_debug():
                io.write_line(f"  <comment>Skipping project checker '{checker.name}' as it cannot check the project.</comment>")
            continue
        buffered_io = BufferedIO(decorated=io.is_decorated())
        exception = checker.check(buffered_io, project, fix)
        if exception is not None:
            io.write_line(f"  <fg=cyan>{checker.name} check issues:</>")
            output = buffered_io.fetch_output()
            if output:
                indented_output = "\n".join([f"    {line}" for line in output.splitlines()])
                io.write_line(indented_output)
            error_output = buffered_io.fetch_error()
            if error_output:
                indented_output = "\n".join([f"    {line}" for line in error_output.splitlines()])
                io.write_line(indented_output)
            return 1
    return 0


def _perform_solution_check(di: DI, projects: list[Project], solution_checkers: list[ISolutionCheck], fix: bool) -> int:
    if not solution_checkers:
        return 0
    io = di.resolve(IO)
    assert io is not None
    io.write_line("<info>Performing solution-wide checks</info>")
    for checker in solution_checkers:
        if not checker.can_check(projects):
            if io.is_debug():
                io.write_line(f"<comment>Skipping solution checker '{checker.name}' as it cannot check the provided projects.</comment>")
            continue
        io.write_line(f" - <comment>{checker.name}</comment>")
        exception = checker.check(io, projects, fix)
        if exception is not None:
            io.write_line(f"<error>{exception}</error>")
            return 1
    return 0


_builtin_project_checks = [
    ProjectPoetryCheck,
]

_builtin_solution_checks = [
    SolutionRuffCheck,
]


class CheckModule(
    NameAwareProtocol,
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol
):
    name: ClassVar[str] = "ps-check"

    def __init__(self, di: DI) -> None:
        for check_cls in _builtin_project_checks:
            di.register(IProjectCheck).implementation(check_cls)
        for check_cls in _builtin_solution_checks:
            di.register(ISolutionCheck).implementation(check_cls)
        self._di = di
        self._exit_code = 0

    def handle_activate(self, application: Application) -> bool:
        # Extend the CheckCommand with an optional "inputs" argument
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
        return True

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        if not isinstance(event.command, CheckCommand):
            return
        # Disable the original command execution
        event.disable_command()

        environment = self._di.resolve(Environment)
        assert environment is not None

        # Filter projects based on inputs
        inputs = _get_inputs(event.io.input)
        filtered_projects = filter_projects(inputs, environment.projects)
        if not filtered_projects:
            event.io.write_line("<comment>No projects found to check.</comment>")
            return

        # Get the "fix" option
        fix = _get_fix_option(event.io.input)

        # Resolve plugin settings
        plugin_settings = environment.host_project.plugin_settings
        check_settings = CheckSettings.model_validate(plugin_settings.model_dump(), by_alias=True)

        # Resolve available project checkers
        available_project_checkers = self._di.resolve_many(IProjectCheck)
        project_checkers = _filter_checkers(available_project_checkers, check_settings, event.io, "Project")
        available_solution_checkers = self._di.resolve_many(ISolutionCheck)
        solution_checkers = _filter_checkers(available_solution_checkers, check_settings, event.io, "Solution")

        if fix:
            event.io.write_line("<fg=magenta>Automatic fix enabled</>")
        event.io.write_line(f"<info>Checking <comment>{len(filtered_projects)}</comment> project(s)")
        for project in filtered_projects:
            self._exit_code = _perform_project_check(self._di, project, project_checkers, fix) if self._exit_code == 0 else self._exit_code
        if self._exit_code != 0:
            event.io.write_line("<fg=yellow>Project checks completed with issues. Solution checks will be skipped.</>")
            return
        self._exit_code = _perform_solution_check(self._di, filtered_projects, solution_checkers, fix)

    def handle_terminate(self, event: ConsoleTerminateEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        event.set_exit_code(self._exit_code)

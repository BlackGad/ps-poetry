from ps.plugin.sdk.setup_extension_template import ExtensionTemplateQuestion


class BlankClassTemplate:
    name: str = "Entry class"
    description: str = "Class-based extension module with all poetry handler functions"
    dependencies: list[str] = ["poetry"]
    questions: list[ExtensionTemplateQuestion] = []
    template: str = '''\
from typing import ClassVar

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_error_event import ConsoleErrorEvent
from cleo.events.console_signal_event import ConsoleSignalEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from poetry.console.application import Application


class ExtensionModule:
    name: ClassVar[str] = "{name}"

    # Called during plugin activation. Return False to disable the module.
    def poetry_activate(self, application: Application) -> bool:
        print("Hello from extension {name}")
        return True

    # Called on console command events.
    def poetry_command(self, event: ConsoleCommandEvent) -> None:
        print("Command event in {name}")

    # Called after command completion.
    def poetry_terminate(self, event: ConsoleTerminateEvent) -> None:
        print("Terminate event in {name}")

    # Called on command errors.
    def poetry_error(self, event: ConsoleErrorEvent) -> None:
        print("Error event in {name}")

    # Called on OS signal events.
    def poetry_signal(self, event: ConsoleSignalEvent) -> None:
        print("Signal event in {name}")
'''

    def prepare_variables(self, variables: dict[str, str]) -> dict[str, str]:
        return variables

from ps.plugin.sdk.setup_extension_template import ExtensionTemplateQuestion


class BlankFunctionTemplate:
    name: str = "Entry functions"
    description: str = "Function-based extension module with all poetry handler functions"
    dependencies: list[str] = ["poetry"]
    questions: list[ExtensionTemplateQuestion] = []
    template: str = '''\
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_error_event import ConsoleErrorEvent
from cleo.events.console_signal_event import ConsoleSignalEvent
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from poetry.console.application import Application


# Called during plugin activation. Return False to disable the module.
def poetry_activate_{snake_name}(application: Application) -> bool:
    print("Hello from extension {snake_name}")
    return True


# Called on console command events.
def poetry_command_{snake_name}(event: ConsoleCommandEvent) -> None:
    print("Command event in {snake_name}")


# Called after command completion.
def poetry_terminate_{snake_name}(event: ConsoleTerminateEvent) -> None:
    print("Terminate event in {snake_name}")


# Called on command errors.
def poetry_error_{snake_name}(event: ConsoleErrorEvent) -> None:
    print("Error event in {snake_name}")


# Called on OS signal events.
def poetry_signal_{snake_name}(event: ConsoleSignalEvent) -> None:
    print("Signal event in {snake_name}")
'''

    def prepare_variables(self, variables: dict[str, str]) -> dict[str, str]:
        return variables

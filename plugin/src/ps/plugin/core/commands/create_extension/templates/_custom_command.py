from ps.plugin.sdk.setup_extension_template import ExtensionTemplateQuestion


class CustomCommandTemplate:
    name: str = "Custom command"
    description: str = "Module with a custom Poetry command"
    dependencies: list[str] = ["poetry"]
    questions: list[ExtensionTemplateQuestion] = [
        ExtensionTemplateQuestion(name="command_name", prompt="Command name:"),
    ]
    template: str = '''\
from cleo.commands.command import Command
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from poetry.console.application import Application


class CustomCommand(Command):
    name = "{command_name}"
    description = ""
    arguments = [
        Argument(
            name="arg-value",
            description="A single argument value",
            default=None,
            required=False),
        Argument(
            name="arg-list",
            description="A list of arguments",
            is_list=True,
            required=False),
    ]
    options = [
        Option("--flag", flag=True, requires_value=False, shortcut="j", description="Flag option"),
        Option("--input", flag=False, requires_value=True, shortcut="i", default=None, description="Input option"),
        Option("--list", flag=False, requires_value=True, is_list=True, shortcut="l", default=[1, 2], description="List option"),
    ]

    def handle(self) -> int:
        print("Handling {command_name}")
        print("Arguments:")
        for arg in self.arguments:
            print(f"  {{arg.name}}: {{self.argument(arg.name)}}")
        print("Options:")
        for opt in self.options:
            print(f"  {{opt.name}}: {{self.option(opt.name)}}")
        return 0


# Called during plugin activation. Return False to disable the module.
def poetry_activate_{snake_name}(application: Application) -> bool:
    application.add(CustomCommand())
    return True

# For advanced use cases, add plugin sdk as a dependency and specify DI in the activate function to spawn the command with dependencies.
# def poetry_activate_{snake_name}(application: Application, di: DI) -> bool:
#     application.add(di.spawn(CustomCommand))
#     return True
'''

    def prepare_variables(self, variables: dict[str, str]) -> dict[str, str]:
        return variables

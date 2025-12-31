from typing import Protocol

from cleo.io.inputs.option import Option
from cleo.io.inputs.argument import Argument


class DefaultOptionProtocol(Protocol):
    options: list[Option]
    arguments: list[Argument]


def ensure_argument(command: DefaultOptionProtocol, argument: Argument) -> bool:
    existing_names = {arg.name for arg in command.arguments}
    if argument.name not in existing_names:
        command.arguments.append(argument)
        return True
    return False


def ensure_option(command: DefaultOptionProtocol, option: Option) -> bool:
    existing_names = {opt.name for opt in command.options}
    if option.name not in existing_names:
        command.options.append(option)
        return True
    return False

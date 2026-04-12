from dataclasses import dataclass
from typing import Optional

from typing_extensions import Protocol, runtime_checkable


@dataclass
class ExtensionTemplateQuestion:
    name: str
    prompt: str
    options: Optional[list[str]] = None
    default: Optional[str] = None


@runtime_checkable
class ExtensionTemplate(Protocol):
    name: str
    description: str
    dependencies: list[str]
    questions: list[ExtensionTemplateQuestion]
    template: str

    def prepare_variables(self, variables: dict[str, str]) -> dict[str, str]:
        ...

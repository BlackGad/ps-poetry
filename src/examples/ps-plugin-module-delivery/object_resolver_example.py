from dataclasses import dataclass

from ps.di import DI
from ps.token_expressions import TokenResolverEntry


@dataclass
class BuildContext:
    author: str
    revision: int

    def __str__(self) -> str:
        return f"{self.author}@{self.revision}"


def poetry_activate(di: DI) -> bool:
    di.register(TokenResolverEntry).factory(lambda: ("build", BuildContext(author="Alice", revision=7)))
    return True

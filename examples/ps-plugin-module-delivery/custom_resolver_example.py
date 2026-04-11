from typing import Optional

from ps.di import DI
from ps.token_expressions import BaseResolver, TokenResolverEntry


class MyResolver(BaseResolver):
    def __call__(self, args: list[str]) -> Optional[str]:
        return args[0] if args else None


def poetry_activate(di: DI) -> bool:
    di.register(TokenResolverEntry).factory(lambda: ("my", MyResolver()))
    return True

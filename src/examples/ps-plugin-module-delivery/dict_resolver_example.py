from ps.di import DI
from ps.token_expressions import TokenResolverEntry


def poetry_activate(di: DI) -> bool:
    di.register(TokenResolverEntry).factory(lambda: ("meta", {"channel": "stable", "environment": "production"}))
    return True

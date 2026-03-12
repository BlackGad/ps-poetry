from typing import Optional

from ps.token_expressions import BaseResolver, ExpressionFactory


class Registry:
    def __init__(self) -> None:
        self.items: dict[str, object] = {}

    def register(self, key: str, value: object) -> None:
        self.items[key] = value


class RegistryResolver(BaseResolver):
    def __init__(self, registry: Registry) -> None:
        self._registry = registry

    def __call__(self, args: list[str]) -> Optional[str]:
        if not args:
            return None
        value = self._registry.items.get(args[0])
        if value is None:
            return None
        if len(args) > 1:
            sub = self.pick_resolver(value)
            if sub is None:
                return None
            result = sub(args[1:])
            return str(result) if result is not None else None
        return str(value)


def main() -> None:
    registry = Registry()
    registry.register("config", {"host": "prod.example.com", "port": 443})
    registry.register("version", "2.5.0")

    factory = ExpressionFactory([("reg", RegistryResolver(registry))])

    print(factory.materialize("{reg:version}"))       # 2.5.0
    print(factory.materialize("{reg:config:host}"))   # prod.example.com
    print(factory.materialize("{reg:config:port}"))   # 443
    print(factory.materialize("{reg:missing<n/a>}"))  # n/a


if __name__ == "__main__":
    main()

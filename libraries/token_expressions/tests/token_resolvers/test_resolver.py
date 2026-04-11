from typing import Any, Optional

from ps.token_expressions import BaseResolver, ExpressionFactory
from ps.token_expressions.token_resolvers._base_resolver import ResolverFactory, TokenResolver


def test_parse_empty_string():
    factory = ExpressionFactory([])
    assert factory.materialize("") == ""


def test_parse_no_tokens():
    factory = ExpressionFactory([])
    assert factory.materialize("simple text") == "simple text"


def test_parse_with_whitespace():
    factory = ExpressionFactory([])
    assert factory.materialize("  text  ") == "  text  "


def test_private_pick_resolver_for_none():
    factory = ExpressionFactory([("none_value", None)])
    assert factory.materialize("{none_value}") == ""


def test_custom_resolver_used_directly():
    class UpperResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return args[0].upper() if args else None

    factory = ExpressionFactory([("up", UpperResolver())])
    assert factory.materialize("{up:hello}") == "HELLO"


def test_custom_resolver_receives_all_args():
    class JoinResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return "-".join(args) if args else None

    factory = ExpressionFactory([("join", JoinResolver())])
    assert factory.materialize("{join:a:b:c}") == "a-b-c"


def test_custom_resolver_not_wrapped_as_instance():
    class SentinelResolver(BaseResolver):
        called_with: Optional[list[str]] = None

        def __call__(self, args: list[str]) -> Optional[str]:
            SentinelResolver.called_with = args
            return "ok"

    factory = ExpressionFactory([("x", SentinelResolver())])
    factory.materialize("{x:foo:bar}")
    assert SentinelResolver.called_with == ["foo", "bar"]


def test_func_resolver_chains_pick_resolver_for_object_result():
    class Config:
        value = "found"

    def resolve_config(_arg: str) -> Config:
        return Config()

    factory = ExpressionFactory([("cfg", resolve_config)])
    assert factory.materialize("{cfg:key:value}") == "found"


def test_custom_resolver_uses_pick_resolver_to_chain():
    class Config:
        value = "chained"

    class ConfigResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            sub = BaseResolver.pick_resolver(Config())
            return sub(args)  # type: ignore[return-value]

    factory = ExpressionFactory([("cfg", ConfigResolver())])
    assert factory.materialize("{cfg:value}") == "chained"


def test_pick_resolver_returns_callable_for_any_value():
    resolver = BaseResolver.pick_resolver({"key": "value"})
    assert callable(resolver)
    assert resolver(["key"]) == "value"


def test_register_resolvers_accepts_list(monkeypatch: Any) -> None:
    monkeypatch.setattr(BaseResolver, "_FACTORIES", [])

    class Marker:
        pass

    called_with: list[Any] = []

    def marker_factory(source: Any) -> Optional[TokenResolver]:
        if isinstance(source, Marker):
            called_with.append(source)
            return lambda args: "marker"  # noqa: ARG005
        return None

    BaseResolver.register_resolvers([marker_factory])
    result = BaseResolver.pick_resolver(Marker())
    assert result([]) == "marker"
    assert len(called_with) == 1


def test_register_resolvers_accepts_generator(monkeypatch: Any) -> None:
    monkeypatch.setattr(BaseResolver, "_FACTORIES", list(BaseResolver._FACTORIES))

    registered: list[ResolverFactory] = []

    def tracking_factory(source: Any) -> Optional[TokenResolver]:
        registered.append(source)
        return None

    def gen() -> Any:
        yield tracking_factory

    BaseResolver.register_resolvers(gen())
    assert tracking_factory in BaseResolver._FACTORIES


def test_register_resolvers_empty_iterable_does_not_change_factories(monkeypatch: Any) -> None:
    monkeypatch.setattr(BaseResolver, "_FACTORIES", list(BaseResolver._FACTORIES))
    before = len(BaseResolver._FACTORIES)
    BaseResolver.register_resolvers([])
    assert len(BaseResolver._FACTORIES) == before


def test_register_resolvers_appends_in_order(monkeypatch: Any) -> None:
    monkeypatch.setattr(BaseResolver, "_FACTORIES", list(BaseResolver._FACTORIES))
    before = len(BaseResolver._FACTORIES)

    f1: ResolverFactory = lambda s: None  # noqa: ARG005, E731
    f2: ResolverFactory = lambda s: None  # noqa: ARG005, E731

    BaseResolver.register_resolvers([f1, f2])
    assert BaseResolver._FACTORIES[before] is f1
    assert BaseResolver._FACTORIES[before + 1] is f2


def test_base_resolver_resolve_factory_returns_self_for_resolver_instance():
    class MyResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return "ok"

    instance = MyResolver()
    result = BaseResolver.resolve_factory(instance)
    assert result is instance


def test_base_resolver_resolve_factory_returns_none_for_non_resolver():
    assert BaseResolver.resolve_factory({"a": 1}) is None
    assert BaseResolver.resolve_factory("string") is None
    assert BaseResolver.resolve_factory(None) is None

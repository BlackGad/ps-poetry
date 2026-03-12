from typing import Optional

from ps.token_expressions import BaseResolver, ExpressionFactory


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
            sub = self.pick_resolver(Config())
            if sub is None:
                return None
            return sub(args)  # type: ignore[return-value]

    factory = ExpressionFactory([("cfg", ConfigResolver())])
    assert factory.materialize("{cfg:value}") == "chained"


def test_custom_resolver_pick_resolver_returns_none_without_bind():
    class StandaloneResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return "ok"

    resolver = StandaloneResolver()
    assert resolver.pick_resolver({}) is None

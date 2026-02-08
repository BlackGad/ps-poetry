from typing import Optional

from ps.token_expressions import ExpressionFactory


def test_materialize_no_resolvers():
    factory = ExpressionFactory([])
    assert factory.materialize("{date:yyyy}") == "{date:yyyy}"


def test_materialize_resolver_order():
    def first_resolver(_args: list[str]) -> Optional[str]:
        return None

    def second_resolver(_args: list[str]) -> Optional[str]:
        return "ok"

    factory = ExpressionFactory([
        ("date", first_resolver),
        ("date", second_resolver),
    ])
    assert factory.materialize("{date:yyyy}") == "ok"


def test_materialize_args_passed():
    def resolver_func(args: list[str]) -> Optional[str]:
        return ",".join(args)

    factory = ExpressionFactory([("rand", resolver_func)])
    assert factory.materialize("{rand:num:min..max}") == "num,min..max"


def test_materialize_casts_values():
    def resolver_func(_args: list[str]) -> Optional[bool]:
        return True

    factory = ExpressionFactory([("flag", resolver_func)])
    assert factory.materialize("{flag}") == "True"


def test_materialize_fallback_used():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing<fallback>}") == "fallback"


def test_materialize_fallback_not_used():
    def resolver_func(_args: list[str]) -> Optional[str]:
        return "resolved"

    factory = ExpressionFactory([("key", resolver_func)])
    assert factory.materialize("{key<fallback>}") == "resolved"


def test_materialize_fallback_empty():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing<>}") == ""


def test_materialize_fallback_with_args():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing:arg1:arg2<fallback>}") == "fallback"


def test_materialize_fallback_numeric():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing<0>}") == "0"
    assert factory.materialize("{missing<23>}") == "23"


def test_materialize_fallback_string_literal():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing<'value'>}") == "'value'"
    assert factory.materialize("{missing<'1.0.0'>}") == "'1.0.0'"


def test_materialize_fallback_boolean():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing<true>}") == "true"
    assert factory.materialize("{missing<false>}") == "false"

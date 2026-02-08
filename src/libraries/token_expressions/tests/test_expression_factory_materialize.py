from typing import Optional

from ps.token_expressions import ExpressionFactory


class Picker:
    def __init__(self, token_resolvers):
        self._factory = ExpressionFactory(token_resolvers)

    def materialize(self, value: str) -> str:
        return self._factory.materialize(value)


def test_picker_materialize_no_resolvers():
    picker = Picker([])
    assert picker.materialize("{date:yyyy}") == "{date:yyyy}"


def test_picker_materialize_resolver_order():
    def first_resolver(_args: list[str]) -> Optional[str]:
        return None

    def second_resolver(_args: list[str]) -> Optional[str]:
        return "ok"

    picker = Picker([
        ("date", first_resolver),
        ("date", second_resolver),
    ])
    assert picker.materialize("{date:yyyy}") == "ok"


def test_picker_materialize_args_passed():
    def resolver_func(args: list[str]) -> Optional[str]:
        return ",".join(args)

    picker = Picker([("rand", resolver_func)])
    assert picker.materialize("{rand:num:min..max}") == "num,min..max"


def test_picker_materialize_casts_values():
    def resolver_func(_args: list[str]) -> Optional[bool]:
        return True

    picker = Picker([("flag", resolver_func)])
    assert picker.materialize("{flag}") == "True"


def test_picker_materialize_fallback_used():
    picker = Picker([])
    assert picker.materialize("{missing<fallback>}") == "fallback"


def test_picker_materialize_fallback_not_used():
    def resolver_func(_args: list[str]) -> Optional[str]:
        return "resolved"

    picker = Picker([("key", resolver_func)])
    assert picker.materialize("{key<fallback>}") == "resolved"


def test_picker_materialize_fallback_empty():
    picker = Picker([])
    assert picker.materialize("{missing<>}") == ""


def test_picker_materialize_fallback_with_args():
    picker = Picker([])
    assert picker.materialize("{missing:arg1:arg2<fallback>}") == "fallback"


def test_picker_materialize_fallback_numeric():
    picker = Picker([])
    assert picker.materialize("{missing<0>}") == "0"
    assert picker.materialize("{missing<23>}") == "23"


def test_picker_materialize_fallback_string_literal():
    picker = Picker([])
    assert picker.materialize("{missing<'value'>}") == "'value'"
    assert picker.materialize("{missing<'1.0.0'>}") == "'1.0.0'"


def test_picker_materialize_fallback_boolean():
    picker = Picker([])
    assert picker.materialize("{missing<true>}") == "true"
    assert picker.materialize("{missing<false>}") == "false"

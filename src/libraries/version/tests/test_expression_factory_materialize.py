from typing import Optional

from ps.version import VersionPicker


def test_picker_materialize_no_resolvers():
    picker = VersionPicker([])
    assert picker.materialize("{date:yyyy}") == "{date:yyyy}"


def test_picker_materialize_resolver_order():
    def first_resolver(_args: list[str]) -> Optional[str]:
        return None

    def second_resolver(_args: list[str]) -> Optional[str]:
        return "ok"

    picker = VersionPicker([
        ("date", first_resolver),
        ("date", second_resolver),
    ])
    assert picker.materialize("{date:yyyy}") == "ok"


def test_picker_materialize_args_passed():
    def resolver_func(args: list[str]) -> Optional[str]:
        return ",".join(args)

    picker = VersionPicker([("rand", resolver_func)])
    assert picker.materialize("{rand:num:min..max}") == "num,min..max"


def test_picker_materialize_casts_values():
    def resolver_func(_args: list[str]) -> Optional[bool]:
        return True

    picker = VersionPicker([("flag", resolver_func)])
    assert picker.materialize("{flag}") == "True"


def test_picker_materialize_fallback_used():
    picker = VersionPicker([])
    assert picker.materialize("{missing<fallback>}") == "fallback"


def test_picker_materialize_fallback_not_used():
    def resolver_func(_args: list[str]) -> Optional[str]:
        return "resolved"

    picker = VersionPicker([("key", resolver_func)])
    assert picker.materialize("{key<fallback>}") == "resolved"


def test_picker_materialize_fallback_empty():
    picker = VersionPicker([])
    assert picker.materialize("{missing<>}") == ""


def test_picker_materialize_fallback_with_args():
    picker = VersionPicker([])
    assert picker.materialize("{missing:arg1:arg2<fallback>}") == "fallback"


def test_picker_materialize_fallback_numeric():
    picker = VersionPicker([])
    assert picker.materialize("{missing<0>}") == "0"
    assert picker.materialize("{missing<23>}") == "23"


def test_picker_materialize_fallback_string_literal():
    picker = VersionPicker([])
    assert picker.materialize("{missing<'value'>}") == "'value'"
    assert picker.materialize("{missing<'1.0.0'>}") == "'1.0.0'"


def test_picker_materialize_fallback_boolean():
    picker = VersionPicker([])
    assert picker.materialize("{missing<true>}") == "true"
    assert picker.materialize("{missing<false>}") == "false"

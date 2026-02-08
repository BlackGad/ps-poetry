from typing import Optional

from ps.token_expressions import ExpressionFactory


class Picker:
    def __init__(self, token_resolvers):
        self._factory = ExpressionFactory(token_resolvers)

    def match(self, condition: str) -> bool:
        return self._factory.match(condition)


def test_picker_match_true_literal():
    picker = Picker([])
    assert picker.match("true") is True


def test_picker_match_false_literal():
    picker = Picker([])
    assert picker.match("false") is True  # "false" is non-empty string


def test_picker_match_zero_is_false():
    picker = Picker([])
    assert picker.match("0") is False


def test_picker_match_positive_number_is_true():
    picker = Picker([])
    assert picker.match("1") is True
    assert picker.match("23") is True


def test_picker_match_empty_string_is_false():
    picker = Picker([])
    assert picker.match("") is False


def test_picker_match_quoted_string_is_true():
    picker = Picker([])
    assert picker.match("'some'") is True


def test_picker_match_empty_quoted_string_is_false():
    picker = Picker([])
    assert picker.match("''") is False


def test_picker_match_and_operator():
    picker = Picker([])
    assert picker.match("1 and 1") is True
    assert picker.match("1 and 0") is False
    assert picker.match("0 and 1") is False


def test_picker_match_or_operator():
    picker = Picker([])
    assert picker.match("1 or 0") is True
    assert picker.match("0 or 1") is True
    assert picker.match("0 or 0") is False


def test_picker_match_not_operator():
    picker = Picker([])
    assert picker.match("not 0") is True
    assert picker.match("not 1") is False


def test_picker_match_parentheses():
    picker = Picker([])
    assert picker.match("(1 and 1)") is True
    assert picker.match("(1 or 0)") is True


def test_picker_match_complex_expression():
    picker = Picker([])
    # (true and 'some' or (1 or 23)) and not 0
    # true = non-zero/non-empty, so let's use 1 for true
    assert picker.match("(1 and 'some' or (1 or 23)) and not 0") is True


def test_picker_match_with_tokens():
    def resolver_func(_args: list[str]) -> Optional[str]:
        return "1"

    picker = Picker([("flag", resolver_func)])
    assert picker.match("{flag} and 1") is True


def test_picker_match_with_tokens_and_fallback():
    picker = Picker([])
    assert picker.match("{missing<1>} and 1") is True
    assert picker.match("{missing<0>} or 1") is True

from typing import Optional

from ps.version import VersionPicker


def test_picker_match_true_literal():
    picker = VersionPicker([])
    assert picker.match("true") is True


def test_picker_match_false_literal():
    picker = VersionPicker([])
    assert picker.match("false") is True  # "false" is non-empty string


def test_picker_match_zero_is_false():
    picker = VersionPicker([])
    assert picker.match("0") is False


def test_picker_match_positive_number_is_true():
    picker = VersionPicker([])
    assert picker.match("1") is True
    assert picker.match("23") is True


def test_picker_match_empty_string_is_false():
    picker = VersionPicker([])
    assert picker.match("") is False


def test_picker_match_quoted_string_is_true():
    picker = VersionPicker([])
    assert picker.match("'some'") is True


def test_picker_match_empty_quoted_string_is_false():
    picker = VersionPicker([])
    assert picker.match("''") is False


def test_picker_match_and_operator():
    picker = VersionPicker([])
    assert picker.match("1 and 1") is True
    assert picker.match("1 and 0") is False
    assert picker.match("0 and 1") is False


def test_picker_match_or_operator():
    picker = VersionPicker([])
    assert picker.match("1 or 0") is True
    assert picker.match("0 or 1") is True
    assert picker.match("0 or 0") is False


def test_picker_match_not_operator():
    picker = VersionPicker([])
    assert picker.match("not 0") is True
    assert picker.match("not 1") is False


def test_picker_match_parentheses():
    picker = VersionPicker([])
    assert picker.match("(1 and 1)") is True
    assert picker.match("(1 or 0)") is True


def test_picker_match_complex_expression():
    picker = VersionPicker([])
    # (true and 'some' or (1 or 23)) and not 0
    # true = non-zero/non-empty, so let's use 1 for true
    assert picker.match("(1 and 'some' or (1 or 23)) and not 0") is True


def test_picker_match_with_tokens():
    def resolver_func(_args: list[str]) -> Optional[str]:
        return "1"

    picker = VersionPicker([("flag", resolver_func)])
    assert picker.match("{flag} and 1") is True


def test_picker_match_with_tokens_and_fallback():
    picker = VersionPicker([])
    assert picker.match("{missing<1>} and 1") is True
    assert picker.match("{missing<0>} or 1") is True

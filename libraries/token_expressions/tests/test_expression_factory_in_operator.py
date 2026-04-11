from ps.token_expressions import ExpressionFactory


def test_in_operator_with_list():
    data = [1, 2, 3]
    factory = ExpressionFactory([("items", data)])
    assert factory.match("1 in {items}") is True
    assert factory.match("2 in {items}") is True
    assert factory.match("4 in {items}") is False


def test_in_operator_with_string_list():
    data = ["alpha", "beta", "gamma"]
    factory = ExpressionFactory([("items", data)])
    assert factory.match("'alpha' in {items}") is True
    assert factory.match("'beta' in {items}") is True
    assert factory.match("'delta' in {items}") is False


def test_in_operator_with_mixed_list():
    data = [1, "text", True]
    factory = ExpressionFactory([("mixed", data)])
    assert factory.match("1 in {mixed}") is True
    assert factory.match("'text' in {mixed}") is True
    assert factory.match("True in {mixed}") is True
    assert factory.match("2 in {mixed}") is False


def test_in_operator_with_literal_list():
    factory = ExpressionFactory([])
    assert factory.match("1 in [1, 2, 3]") is True
    assert factory.match("4 in [1, 2, 3]") is False
    assert factory.match("'a' in ['a', 'b', 'c']") is True


def test_in_operator_combined_with_and():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("1 in {nums} and 2 in {nums}") is True
    assert factory.match("1 in {nums} and 4 in {nums}") is False


def test_in_operator_combined_with_or():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("4 in {nums} or 1 in {nums}") is True
    assert factory.match("4 in {nums} or 5 in {nums}") is False


def test_in_operator_with_not():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("not 4 in {nums}") is True
    assert factory.match("not 1 in {nums}") is False


def test_in_operator_with_parentheses():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("(1 in {nums})") is True
    assert factory.match("(4 in {nums})") is False
    assert factory.match("(1 in {nums} or 4 in {nums}) and 2 in {nums}") is True


def test_in_operator_with_boolean_list():
    data = [True, False]
    factory = ExpressionFactory([("flags", data)])
    assert factory.match("True in {flags}") is True
    assert factory.match("False in {flags}") is True


def test_in_operator_with_empty_list():
    data = []
    factory = ExpressionFactory([("empty", data)])
    assert factory.match("1 in {empty}") is False
    assert factory.match("'a' in {empty}") is False


def test_in_operator_complex_expression():
    nums = [1, 2, 3]
    chars = ["a", "b", "c"]
    factory = ExpressionFactory([("nums", nums), ("chars", chars)])
    assert factory.match("(1 in {nums} and 'a' in {chars}) or (4 in {nums})") is True
    assert factory.match("(4 in {nums} or 'a' in {chars}) and 2 in {nums}") is True


def test_validate_in_operator():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    result = factory.validate_match("1 in {nums}")
    assert result.success


def test_validate_in_operator_correct():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    result = factory.validate_match("1 in {nums}")
    assert result.success


def test_in_operator_with_string_contains_char():
    text = "hello world"
    factory = ExpressionFactory([("text", text)])
    assert factory.match("'h' in {text}") is True
    assert factory.match("'o' in {text}") is True
    assert factory.match("'z' in {text}") is False


def test_in_operator_with_string_contains_substring():
    text = "hello world"
    factory = ExpressionFactory([("text", text)])
    assert factory.match("'hello' in {text}") is True
    assert factory.match("'world' in {text}") is True
    assert factory.match("'lo wo' in {text}") is True
    assert factory.match("'xyz' in {text}") is False


def test_in_operator_with_empty_string():
    text = ""
    factory = ExpressionFactory([("text", text)])
    assert factory.match("'a' in {text}") is False
    assert factory.match("'' in {text}") is True  # Empty string is always in any string


def test_in_operator_string_combined_with_and():
    text = "hello world"
    factory = ExpressionFactory([("text", text)])
    assert factory.match("'h' in {text} and 'w' in {text}") is True
    assert factory.match("'h' in {text} and 'z' in {text}") is False


def test_in_operator_string_combined_with_or():
    text = "hello world"
    factory = ExpressionFactory([("text", text)])
    assert factory.match("'z' in {text} or 'h' in {text}") is True
    assert factory.match("'z' in {text} or 'x' in {text}") is False


def test_in_operator_string_with_not():
    text = "hello world"
    factory = ExpressionFactory([("text", text)])
    assert factory.match("not 'z' in {text}") is True
    assert factory.match("not 'h' in {text}") is False


def test_in_operator_mixed_string_and_list():
    text = "hello"
    nums = [1, 2, 3]
    factory = ExpressionFactory([("text", text), ("nums", nums)])
    assert factory.match("'h' in {text} and 1 in {nums}") is True
    assert factory.match("'z' in {text} or 2 in {nums}") is True
    assert factory.match("'h' in {text} and 5 in {nums}") is False


def test_in_operator_literal_string():
    factory = ExpressionFactory([])
    assert factory.match("'a' in 'abc'") is True
    assert factory.match("'x' in 'abc'") is False
    assert factory.match("'ab' in 'abc'") is True


def test_not_in_operator_with_list():
    data = [1, 2, 3]
    factory = ExpressionFactory([("items", data)])
    assert factory.match("1 not in {items}") is False
    assert factory.match("4 not in {items}") is True
    assert factory.match("2 not in {items}") is False


def test_not_in_operator_with_string():
    text = "hello world"
    factory = ExpressionFactory([("text", text)])
    assert factory.match("'h' not in {text}") is False
    assert factory.match("'z' not in {text}") is True
    assert factory.match("'world' not in {text}") is False
    assert factory.match("'xyz' not in {text}") is True


def test_not_in_operator_literal_list():
    factory = ExpressionFactory([])
    assert factory.match("1 not in [1, 2, 3]") is False
    assert factory.match("4 not in [1, 2, 3]") is True


def test_not_in_operator_combined_with_and():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("4 not in {nums} and 5 not in {nums}") is True
    assert factory.match("1 not in {nums} and 4 not in {nums}") is False


def test_not_in_operator_combined_with_or():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("1 not in {nums} or 4 not in {nums}") is True
    assert factory.match("1 not in {nums} or 2 not in {nums}") is False


def test_not_in_operator_with_parentheses():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    assert factory.match("(1 not in {nums})") is False
    assert factory.match("(4 not in {nums})") is True
    assert factory.match("(1 not in {nums} or 4 not in {nums}) and 2 in {nums}") is True


def test_not_in_vs_not_and_in():
    data = [1, 2, 3]
    factory = ExpressionFactory([("nums", data)])
    # These should be identical - "not in" vs "not" followed by "in"
    assert factory.match("1 not in {nums}") == factory.match("not 1 in {nums}")
    assert factory.match("4 not in {nums}") == factory.match("not 4 in {nums}")


def test_not_in_operator_complex_expression():
    nums = [1, 2, 3]
    chars = ["a", "b", "c"]
    factory = ExpressionFactory([("nums", nums), ("chars", chars)])
    assert factory.match("(4 not in {nums} and 'd' not in {chars}) or 1 in {nums}") is True
    assert factory.match("(1 not in {nums} or 'a' not in {chars}) and 2 in {nums}") is False

from ps.token_expressions import ExpressionFactory


def test_parse_empty_string():
    factory = ExpressionFactory([])
    assert factory.materialize("") == ""


def test_parse_no_tokens():
    factory = ExpressionFactory([])
    assert factory.materialize("simple text") == "simple text"


def test_parse_with_whitespace():
    factory = ExpressionFactory([])
    assert factory.materialize("  text  ") == "  text  "

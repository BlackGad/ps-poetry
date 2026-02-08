from ps.token_expressions import ExpressionFactory


class Picker:
    def __init__(self, token_resolvers):
        self._factory = ExpressionFactory(token_resolvers)

    def materialize(self, value: str) -> str:
        return self._factory.materialize(value)


def test_parse_empty_string():
    picker = Picker([])
    assert picker.materialize("") == ""


def test_parse_no_tokens():
    picker = Picker([])
    assert picker.materialize("simple text") == "simple text"


def test_parse_with_whitespace():
    picker = Picker([])
    assert picker.materialize("  text  ") == "  text  "

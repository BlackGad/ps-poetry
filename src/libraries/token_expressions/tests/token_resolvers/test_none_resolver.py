from ps.token_expressions import ExpressionFactory


def test_none_returns_empty_string():
    factory = ExpressionFactory([("none", None)])
    assert factory.materialize("{none}") == ""


def test_none_with_args_returns_empty_string():
    factory = ExpressionFactory([("none", None)])
    assert factory.materialize("{none:arg1}") == ""
    assert factory.materialize("{none:arg1:arg2}") == ""


def test_none_in_text():
    factory = ExpressionFactory([("none", None)])
    assert factory.materialize("value: {none}") == "value: "
    assert factory.materialize("prefix_{none}_suffix") == "prefix__suffix"


def test_multiple_none_tokens():
    factory = ExpressionFactory([("none", None)])
    assert factory.materialize("{none}{none}") == ""
    assert factory.materialize("{none} and {none}") == " and "

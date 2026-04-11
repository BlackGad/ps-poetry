from ps.token_expressions import ExpressionFactory


def test_list_resolver_empty_args():
    data = [1, 2, 3]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items}") == "[1, 2, 3]"


def test_list_resolver_simple_access():
    data = ["alpha", "beta", "gamma"]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:0}") == "alpha"
    assert factory.materialize("{items:1}") == "beta"
    assert factory.materialize("{items:2}") == "gamma"


def test_list_resolver_numeric_values():
    data = [10, 20, 30]
    factory = ExpressionFactory([("nums", data)])
    assert factory.materialize("{nums:0}") == "10"
    assert factory.materialize("{nums:1}") == "20"
    assert factory.materialize("{nums:2}") == "30"


def test_list_resolver_boolean_values():
    data = [True, False, True]
    factory = ExpressionFactory([("flags", data)])
    assert factory.materialize("{flags:0}") == "True"
    assert factory.materialize("{flags:1}") == "False"
    assert factory.materialize("{flags:2}") == "True"


def test_list_resolver_out_of_bounds():
    data = ["a", "b", "c"]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:3}") == "{items:3}"
    assert factory.materialize("{items:99}") == "{items:99}"


def test_list_resolver_negative_index():
    data = ["a", "b", "c"]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:-1}") == "{items:-1}"


def test_list_resolver_invalid_index():
    data = ["a", "b", "c"]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:invalid}") == "{items:invalid}"
    assert factory.materialize("{items:1.5}") == "{items:1.5}"


def test_list_resolver_nested_list():
    data = [["a", "b"], ["c", "d"]]
    factory = ExpressionFactory([("matrix", data)])
    assert factory.materialize("{matrix:0:0}") == "a"
    assert factory.materialize("{matrix:0:1}") == "b"
    assert factory.materialize("{matrix:1:0}") == "c"
    assert factory.materialize("{matrix:1:1}") == "d"


def test_list_resolver_nested_dict():
    data = [{"name": "first", "value": 1}, {"name": "second", "value": 2}]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:0:name}") == "first"
    assert factory.materialize("{items:0:value}") == "1"
    assert factory.materialize("{items:1:name}") == "second"
    assert factory.materialize("{items:1:value}") == "2"


def test_list_resolver_nested_object():
    class Item:
        def __init__(self, name: str):
            self.name = name

    data = [Item("first"), Item("second")]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:0:name}") == "first"
    assert factory.materialize("{items:1:name}") == "second"


def test_list_resolver_deep_nested():
    data = [[["deep"]]]
    factory = ExpressionFactory([("data", data)])
    assert factory.materialize("{data:0:0:0}") == "deep"


def test_list_resolver_mixed_types():
    data = ["text", 42, True]
    factory = ExpressionFactory([("mixed", data)])
    assert factory.materialize("{mixed:0}") == "text"
    assert factory.materialize("{mixed:1}") == "42"
    assert factory.materialize("{mixed:2}") == "True"


def test_list_resolver_none_value():
    data = ["value", None]
    factory = ExpressionFactory([("items", data)])
    assert factory.materialize("{items:0}") == "value"
    assert factory.materialize("{items:1}") == "{items:1}"


def test_dict_with_list_value():
    data = {"items": ["a", "b", "c"]}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:items:0}") == "a"
    assert factory.materialize("{config:items:1}") == "b"
    assert factory.materialize("{config:items:2}") == "c"


def test_list_with_dict_with_list():
    data = [{"values": [1, 2, 3]}]
    factory = ExpressionFactory([("data", data)])
    assert factory.materialize("{data:0:values:0}") == "1"
    assert factory.materialize("{data:0:values:1}") == "2"
    assert factory.materialize("{data:0:values:2}") == "3"

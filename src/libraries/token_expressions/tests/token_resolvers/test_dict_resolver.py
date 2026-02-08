from typing import Optional

from ps.token_expressions import ExpressionFactory


def test_dict_resolver_simple_access():
    data = {"version": "1.2.3", "build": 456}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:version}") == "1.2.3"
    assert factory.materialize("{config:build}") == "456"


def test_dict_resolver_missing_key():
    data = {"version": "1.2.3"}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:missing}") == "{config:missing}"


def test_dict_resolver_nested_dict():
    data = {"app": {"version": "2.0.0", "name": "test"}}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:app:version}") == "2.0.0"
    assert factory.materialize("{config:app:name}") == "test"


def test_dict_resolver_deep_nested():
    data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:level1:level2:level3:value}") == "deep"


def test_dict_resolver_nested_missing():
    data = {"level1": {"level2": "value"}}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:level1:missing}") == "{config:level1:missing}"


def test_dict_resolver_mixed_types():
    data = {"string": "text", "number": 42, "bool": True}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:string}") == "text"
    assert factory.materialize("{config:number}") == "42"
    assert factory.materialize("{config:bool}") == "True"


def test_dict_with_object_values():
    class SimpleObject:
        def __init__(self):
            self.value = "obj_value"

    data = {"obj": SimpleObject()}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:obj:value}") == "obj_value"


def test_dict_with_nested_object():
    class Inner:
        def __init__(self):
            self.level = "inner"

    class Outer:
        def __init__(self):
            self.inner = Inner()

    data = {"outer": Outer()}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:outer:inner:level}") == "inner"


def test_dict_empty_args():
    data = {"key": "value"}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config}") == "{config}"


def test_dict_none_value():
    data = {"key": None}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:key}") == "{config:key}"


def test_dict_with_dict_containing_none():
    data = {"level1": {"level2": None}}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:level1:level2}") == "{config:level1:level2}"


def test_mixed_dict_and_instance():
    class Config:
        def __init__(self):
            self.settings = {"debug": True, "port": 8080}

    config = Config()
    factory = ExpressionFactory([("app", config)])
    assert factory.materialize("{app:settings:debug}") == "True"
    assert factory.materialize("{app:settings:port}") == "8080"


def test_mixed_instance_and_dict():
    class Server:
        def __init__(self):
            self.port = 3000

    data = {"server": Server()}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:server:port}") == "3000"


def test_function_resolver():
    def my_func(args: list[str]) -> Optional[str]:
        if args and args[0] == "version":
            return "1.0.0"
        return None

    factory = ExpressionFactory([("func", my_func)])
    assert factory.materialize("{func:version}") == "1.0.0"
    assert factory.materialize("{func:other}") == "{func:other}"


def test_mixed_resolvers():
    def func_resolver(_args: list[str]) -> Optional[str]:
        return "from_func"

    data = {"key": "from_dict"}

    class Instance:
        def __init__(self):
            self.value = "from_instance"

    factory = ExpressionFactory([
        ("func", func_resolver),
        ("dict", data),
        ("inst", Instance()),
    ])
    assert factory.materialize("{func:anything}") == "from_func"
    assert factory.materialize("{dict:key}") == "from_dict"
    assert factory.materialize("{inst:value}") == "from_instance"


def test_dict_list_value():
    data = {"items": [1, 2, 3]}
    factory = ExpressionFactory([("config", data)])
    assert factory.materialize("{config:items}") == "{config:items}"

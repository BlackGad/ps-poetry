from typing import Optional

from ps.token_expressions import BaseResolver, ExpressionFactory


def test_materialize_single_recursion():
    def level1_resolver(_arg: str) -> str:
        return "{level2}"

    def level2_resolver(_arg: str) -> str:
        return "final"

    factory = ExpressionFactory([("level1", level1_resolver), ("level2", level2_resolver)])
    result = factory.materialize("{level1}")
    assert result == "final"


def test_materialize_multiple_recursion():
    def level1_resolver(_arg: str) -> str:
        return "{level2}_{level2}"

    def level2_resolver(_arg: str) -> str:
        return "{level3}"

    def level3_resolver(_arg: str) -> str:
        return "value"

    factory = ExpressionFactory([
        ("level1", level1_resolver),
        ("level2", level2_resolver),
        ("level3", level3_resolver),
    ])
    result = factory.materialize("{level1}")
    assert result == "value_value"


def test_materialize_max_depth_default():
    def recursive_resolver(_arg: str) -> str:
        return "{recursive}"

    factory = ExpressionFactory([("recursive", recursive_resolver)])
    result = factory.materialize("{recursive}")
    # Should stop after 3 iterations
    assert result == "{recursive}"


def test_materialize_max_depth_custom():
    factory = ExpressionFactory(
        [("track", lambda _: "{track}")],
        max_recursion_depth=5
    )
    result = factory.materialize("{track}")
    # After 5 iterations of no changes (always returns same token), should stop
    assert result == "{track}"


def test_materialize_partial_recursion():
    def resolver(arg: str) -> str:
        if arg == "nested":
            return "prefix_{key}_suffix"
        return "final"

    factory = ExpressionFactory([("key", resolver)])
    result = factory.materialize("{key:nested}")
    assert result == "prefix_final_suffix"


def test_materialize_mixed_recursive_and_static():
    def dynamic_resolver(_arg: str) -> str:
        return "{static}"

    factory = ExpressionFactory([
        ("dynamic", dynamic_resolver),
        ("static", lambda _: "value"),
    ])
    result = factory.materialize("start_{dynamic}_end")
    assert result == "start_value_end"


def test_materialize_recursive_with_fallback():
    def level1_resolver(_arg: str) -> str:
        return "{missing<fallback>}"

    factory = ExpressionFactory([("level1", level1_resolver)])
    result = factory.materialize("{level1}")
    assert result == "fallback"


def test_materialize_recursive_with_args():
    def builder(arg: str) -> str:
        if arg == "nested":
            return "{value:arg1}"
        return ""

    def value_resolver(arg: str) -> str:
        return arg or "empty"

    factory = ExpressionFactory([("builder", builder), ("value", value_resolver)])
    result = factory.materialize("{builder:nested}")
    assert result == "arg1"


def test_materialize_circular_reference_protection():
    def a_resolver(_arg: str) -> str:
        return "{b}"

    def b_resolver(_arg: str) -> str:
        return "{a}"

    factory = ExpressionFactory([("a", a_resolver), ("b", b_resolver)])
    result = factory.materialize("{a}")
    # Should stop at max depth and return unresolved token
    assert "{" in result


def test_materialize_depth_one():
    def level1_resolver(_arg: str) -> str:
        return "{level2}"

    def level2_resolver(_arg: str) -> str:
        return "final"

    factory = ExpressionFactory(
        [("level1", level1_resolver), ("level2", level2_resolver)],
        max_recursion_depth=1
    )
    result = factory.materialize("{level1}")
    # Only one iteration, so it returns {level2}
    assert result == "{level2}"


def test_validate_materialize_recursive_tokens():
    def level1_resolver(_arg: str) -> str:
        return "{level2}"

    def level2_resolver(_arg: str) -> str:
        return "{missing}"

    factory = ExpressionFactory([("level1", level1_resolver), ("level2", level2_resolver)])
    result = factory.validate_materialize("{level1}")
    assert result.success is False
    assert len(result.errors) == 1
    # Should detect the missing resolver in the nested token


def test_validate_materialize_recursive_with_fallback():
    def level1_resolver(_arg: str) -> str:
        return "{missing<default>}"

    factory = ExpressionFactory([("level1", level1_resolver)])
    result = factory.validate_materialize("{level1}")
    assert result.success is True


def test_validate_materialize_deep_recursion():
    def level1_resolver(_arg: str) -> str:
        return "{level2}"

    def level2_resolver(_arg: str) -> str:
        return "{level3}"

    def level3_resolver(_arg: str) -> str:
        return "{level4}"  # level4 doesn't exist

    factory = ExpressionFactory([
        ("level1", level1_resolver),
        ("level2", level2_resolver),
        ("level3", level3_resolver),
    ])
    result = factory.validate_materialize("{level1}")
    assert result.success is False


def test_materialize_complex_recursive_template():
    def env_name_resolver(_arg: str) -> str:
        return "production"

    def env_config_resolver(arg: str) -> str:
        env = arg or "dev"
        return f"{{server:{env}}}"

    def server_resolver(arg: str) -> str:
        env = arg or "dev"
        servers = {"production": "prod.example.com", "dev": "localhost"}
        return servers.get(env, "unknown")

    factory = ExpressionFactory([
        ("env", env_name_resolver),
        ("config", env_config_resolver),
        ("server", server_resolver),
    ])

    result = factory.materialize("Connecting to: {config:{env}}")
    assert result == "Connecting to: prod.example.com"


# ---------------------------------------------------------------------------
# Nested argument syntax: {prov1:{prov2}}
# Inner token resolves first, its value becomes the argument for the outer token
# ---------------------------------------------------------------------------


def test_nested_arg_inner_resolves_first():
    factory = ExpressionFactory([
        ("outer", lambda arg: f"got:{arg}" if arg else "no_args"),
        ("inner", lambda _: "inner_value"),
    ])
    assert factory.materialize("{outer:{inner}}") == "got:inner_value"


def test_nested_arg_inner_value_passed_as_arg():
    factory = ExpressionFactory([
        ("prefix", lambda arg: arg.upper() if arg else ""),
        ("key", lambda _: "hello"),
    ])
    assert factory.materialize("{prefix:{key}}") == "HELLO"


def test_nested_arg_inner_with_its_own_arg():
    class OuterResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return f"outer:{':'.join(args)}" if args else ""

    class InnerResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return f"inner:{':'.join(args)}" if args else ""

    factory = ExpressionFactory([
        ("outer", OuterResolver()),
        ("inner", InnerResolver()),
    ])
    assert factory.materialize("{outer:{inner:x}}") == "outer:inner:x"


def test_nested_arg_multiple_outer_args_with_inner():
    class JoinResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return "-".join(args)

    factory = ExpressionFactory([
        ("join", JoinResolver()),
        ("val", lambda _: "mid"),
    ])
    assert factory.materialize("{join:a:{val}:b}") == "a-mid-b"


def test_nested_arg_two_inner_tokens_in_args():
    class FmtResolver(BaseResolver):
        def __call__(self, args: list[str]) -> Optional[str]:
            return f"{args[0]}/{args[1]}" if len(args) >= 2 else ""

    factory = ExpressionFactory([
        ("fmt", FmtResolver()),
        ("year", lambda _: "2026"),
        ("month", lambda _: "03"),
    ])
    assert factory.materialize("{fmt:{year}:{month}}") == "2026/03"


def test_nested_arg_inner_feeds_into_outer_lookup():
    config = {"production": "prod.example.com", "staging": "stg.example.com"}
    factory = ExpressionFactory([
        ("server", config),
        ("env", lambda _: "production"),
    ])
    assert factory.materialize("{server:{env}}") == "prod.example.com"


def test_nested_arg_three_levels_deep():
    factory = ExpressionFactory([
        ("a", lambda arg: f"a({arg})" if arg else "a()"),
        ("b", lambda arg: f"b({arg})" if arg else "b()"),
        ("c", lambda _: "leaf"),
    ])
    assert factory.materialize("{a:{b:{c}}}") == "a(b(leaf))"


def test_nested_arg_unresolved_inner_leaves_outer_unresolved():
    factory = ExpressionFactory([
        ("outer", lambda arg: f"got:{arg}" if arg else "no_args"),
    ])
    result = factory.materialize("{outer:{missing}}")
    assert result == "{outer:{missing}}"

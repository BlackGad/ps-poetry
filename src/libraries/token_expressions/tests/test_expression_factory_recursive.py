from ps.token_expressions import ExpressionFactory


def test_materialize_single_recursion():
    def level1_resolver(_args: list[str]) -> str:
        return "{level2}"

    def level2_resolver(_args: list[str]) -> str:
        return "final"

    factory = ExpressionFactory([("level1", level1_resolver), ("level2", level2_resolver)])
    result = factory.materialize("{level1}")
    assert result == "final"


def test_materialize_multiple_recursion():
    def level1_resolver(_args: list[str]) -> str:
        return "{level2}_{level2}"

    def level2_resolver(_args: list[str]) -> str:
        return "{level3}"

    def level3_resolver(_args: list[str]) -> str:
        return "value"

    factory = ExpressionFactory([
        ("level1", level1_resolver),
        ("level2", level2_resolver),
        ("level3", level3_resolver),
    ])
    result = factory.materialize("{level1}")
    assert result == "value_value"


def test_materialize_max_depth_default():
    def recursive_resolver(_args: list[str]) -> str:
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
    def resolver(args: list[str]) -> str:
        if args and args[0] == "nested":
            return "prefix_{key}_suffix"
        return "final"

    factory = ExpressionFactory([("key", resolver)])
    result = factory.materialize("{key:nested}")
    assert result == "prefix_final_suffix"


def test_materialize_mixed_recursive_and_static():
    def dynamic_resolver(_args: list[str]) -> str:
        return "{static}"

    factory = ExpressionFactory([
        ("dynamic", dynamic_resolver),
        ("static", lambda _: "value"),
    ])
    result = factory.materialize("start_{dynamic}_end")
    assert result == "start_value_end"


def test_materialize_recursive_with_fallback():
    def level1_resolver(_args: list[str]) -> str:
        return "{missing<fallback>}"

    factory = ExpressionFactory([("level1", level1_resolver)])
    result = factory.materialize("{level1}")
    assert result == "fallback"


def test_materialize_recursive_with_args():
    def builder(args: list[str]) -> str:
        if args and args[0] == "nested":
            return "{value:arg1:arg2}"
        return ""

    def value_resolver(args: list[str]) -> str:
        return "_".join(args) if args else "empty"

    factory = ExpressionFactory([("builder", builder), ("value", value_resolver)])
    result = factory.materialize("{builder:nested}")
    assert result == "arg1_arg2"


def test_materialize_circular_reference_protection():
    def a_resolver(_args: list[str]) -> str:
        return "{b}"

    def b_resolver(_args: list[str]) -> str:
        return "{a}"

    factory = ExpressionFactory([("a", a_resolver), ("b", b_resolver)])
    result = factory.materialize("{a}")
    # Should stop at max depth and return unresolved token
    assert "{" in result


def test_materialize_depth_one():
    def level1_resolver(_args: list[str]) -> str:
        return "{level2}"

    def level2_resolver(_args: list[str]) -> str:
        return "final"

    factory = ExpressionFactory(
        [("level1", level1_resolver), ("level2", level2_resolver)],
        max_recursion_depth=1
    )
    result = factory.materialize("{level1}")
    # Only one iteration, so it returns {level2}
    assert result == "{level2}"


def test_validate_materialize_recursive_tokens():
    def level1_resolver(_args: list[str]) -> str:
        return "{level2}"

    def level2_resolver(_args: list[str]) -> str:
        return "{missing}"

    factory = ExpressionFactory([("level1", level1_resolver), ("level2", level2_resolver)])
    result = factory.validate_materialize("{level1}")
    assert result.success is False
    assert len(result.errors) == 1
    # Should detect the missing resolver in the nested token


def test_validate_materialize_recursive_with_fallback():
    def level1_resolver(_args: list[str]) -> str:
        return "{missing<default>}"

    factory = ExpressionFactory([("level1", level1_resolver)])
    result = factory.validate_materialize("{level1}")
    assert result.success is True


def test_validate_materialize_deep_recursion():
    def level1_resolver(_args: list[str]) -> str:
        return "{level2}"

    def level2_resolver(_args: list[str]) -> str:
        return "{level3}"

    def level3_resolver(_args: list[str]) -> str:
        return "{level4}"  # level4 doesn't exist

    factory = ExpressionFactory([
        ("level1", level1_resolver),
        ("level2", level2_resolver),
        ("level3", level3_resolver),
    ])
    result = factory.validate_materialize("{level1}")
    assert result.success is False


def test_materialize_complex_recursive_template():
    def env_name_resolver(_args: list[str]) -> str:
        return "production"

    def env_config_resolver(args: list[str]) -> str:
        env = args[0] if args else "dev"
        return f"{{server:{env}}}"

    def server_resolver(args: list[str]) -> str:
        env = args[0] if args else "dev"
        servers = {"production": "prod.example.com", "dev": "localhost"}
        return servers.get(env, "unknown")

    factory = ExpressionFactory([
        ("env", env_name_resolver),
        ("config", env_config_resolver),
        ("server", server_resolver),
    ])

    result = factory.materialize("Connecting to: {config:{env}}")
    assert result == "Connecting to: prod.example.com"

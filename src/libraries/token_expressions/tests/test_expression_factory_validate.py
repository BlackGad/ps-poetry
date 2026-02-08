from ps.token_expressions import (
    ExpressionFactory,
    FallbackTokenError,
    MissingResolverError,
    UnresolvedTokenError,
)


def test_validate_empty_string():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("")
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_no_tokens():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("plain text without tokens")
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_success_with_resolver():
    def resolver(_args: list[str]) -> str:
        return "value"

    factory = ExpressionFactory([("key", resolver)])
    result = factory.validate_materialize("{key}")
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_success_with_fallback():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing<fallback>}")
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_missing_resolver():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing}")
    assert result.success is False
    assert len(result.errors) == 1
    error = result.errors[0]
    assert isinstance(error, MissingResolverError)
    assert error.key == "missing"
    assert error.token == "{missing}"
    assert error.position == 0


def test_validate_multiple_missing_resolvers():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{first} {second}")
    assert result.success is False
    assert len(result.errors) == 2
    assert isinstance(result.errors[0], MissingResolverError)
    assert result.errors[0].key == "first"
    assert result.errors[0].position == 0
    assert isinstance(result.errors[1], MissingResolverError)
    assert result.errors[1].key == "second"
    assert result.errors[1].position == 8


def test_validate_unresolved_token():
    def resolver(_args: list[str]) -> None:
        return None

    factory = ExpressionFactory([("key", resolver)])
    result = factory.validate_materialize("{key:arg}")
    assert result.success is False
    assert len(result.errors) == 1
    error = result.errors[0]
    assert isinstance(error, UnresolvedTokenError)
    assert error.key == "key"
    assert error.args == ["arg"]
    assert error.token == "{key:arg}"


def test_validate_resolver_returning_none_treated_as_unresolved():
    def failing_resolver(_args: list[str]) -> str:
        raise ValueError("Test error")

    factory = ExpressionFactory([("key", failing_resolver)])
    result = factory.validate_materialize("{key}")
    assert result.success is False
    assert len(result.errors) == 1
    error = result.errors[0]
    assert isinstance(error, UnresolvedTokenError)


def test_validate_mixed_errors():
    def failing_resolver(_args: list[str]) -> str:
        raise RuntimeError("Failure")

    def none_resolver(_args: list[str]) -> None:
        return None

    factory = ExpressionFactory([
        ("failing", failing_resolver),
        ("none", none_resolver),
    ])
    result = factory.validate_materialize("{missing} {failing} {none:arg} {none<ok>}")
    assert result.success is False
    assert len(result.errors) == 3

    assert isinstance(result.errors[0], MissingResolverError)
    assert result.errors[0].key == "missing"

    assert isinstance(result.errors[1], UnresolvedTokenError)
    assert result.errors[1].key == "failing"

    assert isinstance(result.errors[2], UnresolvedTokenError)
    assert result.errors[2].key == "none"


def test_validate_position_tracking():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("text {first} more text {second} end")
    assert result.success is False
    assert len(result.errors) == 2
    assert result.errors[0].position == 5
    assert result.errors[1].position == 23


def test_validate_success_property():
    factory = ExpressionFactory([])

    success_result = factory.validate_materialize("no tokens")
    assert success_result.success is True

    failure_result = factory.validate_materialize("{missing}")
    assert failure_result.success is False


def test_validate_bool_conversion():
    factory = ExpressionFactory([])

    success_result = factory.validate_materialize("no tokens")
    assert bool(success_result) is True

    failure_result = factory.validate_materialize("{missing}")
    assert bool(failure_result) is False


def test_validate_with_args():
    def resolver(args: list[str]) -> str | None:
        if args and args[0] == "valid":
            return "ok"
        return None

    factory = ExpressionFactory([("key", resolver)])

    valid = factory.validate_materialize("{key:valid}")
    assert valid.success is True

    invalid = factory.validate_materialize("{key:invalid}")
    assert invalid.success is False
    assert isinstance(invalid.errors[0], UnresolvedTokenError)
    assert invalid.errors[0].args == ["invalid"]


def test_validate_resolver_exception_treated_as_unresolved():
    def failing_resolver(args: list[str]) -> str:
        raise ValueError(f"Failed with {args}")

    factory = ExpressionFactory([("key", failing_resolver)])
    result = factory.validate_materialize("{key:arg1:arg2}")
    assert result.success is False
    error = result.errors[0]
    assert isinstance(error, UnresolvedTokenError)
    assert error.args == ["arg1", "arg2"]


def test_validate_empty_key_ignored():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{:arg}")
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_resolver_order():
    def first_resolver(_args: list[str]) -> None:
        return None

    def second_resolver(_args: list[str]) -> str:
        return "ok"

    factory = ExpressionFactory([
        ("key", first_resolver),
        ("key", second_resolver),
    ])

    result = factory.validate_materialize("{key}")
    assert result.success is True


def test_validate_resolver_chain_continues_after_exception():
    def first_failing(_args: list[str]) -> str:
        raise ValueError("First fails")

    def second_working(_args: list[str]) -> str:
        return "ok"

    factory = ExpressionFactory([
        ("key", first_failing),
        ("key", second_working),
    ])

    result = factory.validate_materialize("{key}")
    assert result.success is True


def test_validate_complex_template():
    def env_resolver(args: list[str]) -> str | None:
        env_vars = {"USER": "john", "HOME": "/home/john"}
        return env_vars.get(args[0]) if args else None

    config = {"version": "1.0.0", "name": "myapp"}

    factory = ExpressionFactory([
        ("env", env_resolver),
        ("config", config),
    ])

    result = factory.validate_materialize(
        "User: {env:USER}, App: {config:name} v{config:version}, "
        "Missing: {config:missing}, Unknown: {unknown}"
    )

    assert result.success is False
    assert len(result.errors) == 2

    missing_error = next(e for e in result.errors if isinstance(e, UnresolvedTokenError))
    assert missing_error.key == "config"

    unknown_error = next(e for e in result.errors if isinstance(e, MissingResolverError))
    assert unknown_error.key == "unknown"


def test_validate_nested_resolution():
    class Config:
        def __init__(self):
            self.db = {"host": "localhost"}

    factory = ExpressionFactory([("cfg", Config())])

    success = factory.validate_materialize("{cfg:db:host}")
    assert success.success is True

    failure = factory.validate_materialize("{cfg:db:missing}")
    assert failure.success is False
    assert isinstance(failure.errors[0], UnresolvedTokenError)


def test_validation_result_dataclass_immutability():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing}")

    error = result.errors[0]
    assert isinstance(error, MissingResolverError)

    try:
        error.key = "modified"  # type: ignore[misc]
        raise AssertionError("Should not be able to modify frozen dataclass")
    except AttributeError:
        pass


def test_validate_preserves_token_text():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{key:arg1:arg2:arg3}")

    assert result.success is False
    error = result.errors[0]
    assert error.token == "{key:arg1:arg2:arg3}"


def test_validate_fallback_default_behavior():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing<fallback>}")
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_fallback_as_failure():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing<fallback>}", threat_fallback_as_failure=True)
    assert result.success is False
    assert len(result.errors) == 1
    error = result.errors[0]
    assert isinstance(error, FallbackTokenError)
    assert error.key == "missing"
    assert error.token == "{missing<fallback>}"
    assert error.fallback == "fallback"
    assert error.position == 0


def test_validate_fallback_with_resolver_unresolved():
    def resolver(_args: list[str]) -> None:
        return None

    factory = ExpressionFactory([("key", resolver)])
    result = factory.validate_materialize("{key:arg<fallback>}", threat_fallback_as_failure=True)
    assert result.success is False
    assert len(result.errors) == 1
    error = result.errors[0]
    assert isinstance(error, FallbackTokenError)
    assert error.key == "key"
    assert error.args == ["arg"]
    assert error.fallback == "fallback"


def test_validate_fallback_with_resolver_resolved():
    def resolver(_args: list[str]) -> str:
        return "resolved"

    factory = ExpressionFactory([("key", resolver)])
    result = factory.validate_materialize("{key<fallback>}", threat_fallback_as_failure=True)
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_multiple_fallback_tokens():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{first<a>} {second<b>}", threat_fallback_as_failure=True)
    assert result.success is False
    assert len(result.errors) == 2
    assert isinstance(result.errors[0], FallbackTokenError)
    assert result.errors[0].key == "first"
    assert result.errors[0].fallback == "a"
    assert result.errors[0].position == 0
    assert isinstance(result.errors[1], FallbackTokenError)
    assert result.errors[1].key == "second"
    assert result.errors[1].fallback == "b"
    assert result.errors[1].position == 11


def test_validate_mixed_fallback_and_missing():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing} {fallback<value>}", threat_fallback_as_failure=True)
    assert result.success is False
    assert len(result.errors) == 2
    assert isinstance(result.errors[0], MissingResolverError)
    assert result.errors[0].key == "missing"
    assert isinstance(result.errors[1], FallbackTokenError)
    assert result.errors[1].key == "fallback"


def test_validate_fallback_dataclass_properties():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{key:arg1:arg2<default>}", threat_fallback_as_failure=True)
    error = result.errors[0]
    assert isinstance(error, FallbackTokenError)
    assert error.token == "{key:arg1:arg2<default>}"
    assert error.position == 0
    assert error.key == "key"
    assert error.args == ["arg1", "arg2"]
    assert error.fallback == "default"


def test_validate_fallback_dataclass_immutability():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing<fallback>}", threat_fallback_as_failure=True)
    error = result.errors[0]
    assert isinstance(error, FallbackTokenError)

    try:
        error.fallback = "modified"  # type: ignore[misc]
        raise AssertionError("Should not be able to modify frozen dataclass")
    except AttributeError:
        pass


def test_validate_fallback_parameter_false():
    factory = ExpressionFactory([])
    result = factory.validate_materialize("{missing<fallback>}", threat_fallback_as_failure=False)
    assert result.success is True
    assert len(result.errors) == 0


def test_validate_complex_with_fallback_as_failure():
    def resolver(args: list[str]) -> str | None:
        if args and args[0] == "valid":
            return "ok"
        return None

    factory = ExpressionFactory([("key", resolver)])
    result = factory.validate_materialize(
        "{key:valid} {key:invalid<fallback>} {missing} {key:another<backup>}",
        threat_fallback_as_failure=True
    )
    assert result.success is False
    assert len(result.errors) == 3

    assert isinstance(result.errors[0], FallbackTokenError)
    assert result.errors[0].key == "key"
    assert result.errors[0].fallback == "fallback"

    assert isinstance(result.errors[1], MissingResolverError)
    assert result.errors[1].key == "missing"

    assert isinstance(result.errors[2], FallbackTokenError)
    assert result.errors[2].key == "key"
    assert result.errors[2].fallback == "backup"


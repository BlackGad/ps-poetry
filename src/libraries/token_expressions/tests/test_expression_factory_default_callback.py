from ps.token_expressions import ExpressionFactory


def test_default_callback_no_args():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing}") == "{missing}"


def test_default_callback_with_args():
    factory = ExpressionFactory([])
    assert factory.materialize("{missing:arg1}") == "{missing:arg1}"
    assert factory.materialize("{missing:arg1:arg2}") == "{missing:arg1:arg2}"
    assert factory.materialize("{missing:arg1:arg2:arg3}") == "{missing:arg1:arg2:arg3}"


def test_default_callback_not_called_when_resolved():
    def resolver_func(_args: list[str]) -> str:
        return "resolved"

    def custom_callback(_key: str, _args: list[str]) -> str:
        return "should_not_be_called"

    factory = ExpressionFactory([("key", resolver_func)], custom_callback)
    assert factory.materialize("{key:arg}") == "resolved"


def test_default_callback_not_called_when_fallback_used():
    def custom_callback(_key: str, _args: list[str]) -> str:
        return "should_not_be_called"

    factory = ExpressionFactory([], custom_callback)
    assert factory.materialize("{missing<fallback>}") == "fallback"


def test_custom_default_callback_simple():
    def custom_callback(key: str, _args: list[str]) -> str:
        return f"CUSTOM:{key}"

    factory = ExpressionFactory([], custom_callback)
    assert factory.materialize("{missing}") == "CUSTOM:missing"
    assert factory.materialize("{other}") == "CUSTOM:other"


def test_custom_default_callback_with_args():
    def custom_callback(key: str, args: list[str]) -> str:
        return f"{key}[{','.join(args)}]"

    factory = ExpressionFactory([], custom_callback)
    assert factory.materialize("{missing:arg1}") == "missing[arg1]"
    assert factory.materialize("{missing:arg1:arg2}") == "missing[arg1,arg2]"


def test_custom_default_callback_returns_int():
    def custom_callback(_key: str, _args: list[str]) -> int:
        return 0

    factory = ExpressionFactory([], custom_callback)
    assert factory.materialize("{missing}") == "0"


def test_custom_default_callback_returns_bool():
    def custom_callback(_key: str, _args: list[str]) -> bool:
        return True

    factory = ExpressionFactory([], custom_callback)
    assert factory.materialize("{missing}") == "True"


def test_default_callback_mixed_resolved_and_missing():
    def resolver_func(args: list[str]) -> str | None:
        if args and args[0] == "exists":
            return "found"
        return None

    factory = ExpressionFactory([("key", resolver_func)])
    result = factory.materialize("{key:exists} and {key:missing}")
    assert result == "found and {key:missing}"


def test_default_callback_multiple_missing_tokens():
    factory = ExpressionFactory([])
    result = factory.materialize("{first} {second:arg} {third:a:b}")
    assert result == "{first} {second:arg} {third:a:b}"


def test_custom_callback_logging_pattern():
    calls = []

    def logging_callback(key: str, args: list[str]) -> str:
        calls.append((key, args))
        return "UNRESOLVED"

    factory = ExpressionFactory([], logging_callback)
    factory.materialize("{missing:arg1} {other:arg2:arg3}")

    assert len(calls) == 2
    assert calls[0] == ("missing", ["arg1"])
    assert calls[1] == ("other", ["arg2", "arg3"])


def test_default_callback_empty_key():
    factory = ExpressionFactory([])
    assert factory.materialize("{:arg<fallback>}") == "fallback"


def test_custom_callback_with_empty_args():
    def custom_callback(key: str, args: list[str]) -> str:
        return f"{key}:{len(args)}"

    factory = ExpressionFactory([], custom_callback)
    assert factory.materialize("{missing}") == "missing:0"
    assert factory.materialize("{missing:arg}") == "missing:1"


def test_default_callback_preserves_special_chars_in_args():
    factory = ExpressionFactory([])
    assert factory.materialize("{key:arg.with.dots}") == "{key:arg.with.dots}"
    assert factory.materialize("{key:arg-with-dash}") == "{key:arg-with-dash}"
    assert factory.materialize("{key:arg_with_under}") == "{key:arg_with_under}"


def test_custom_callback_error_handling():
    def error_callback(key: str, _args: list[str]) -> str:
        if key == "error":
            return "ERROR"
        return "OK"

    factory = ExpressionFactory([], error_callback)
    assert factory.materialize("{error}") == "ERROR"
    assert factory.materialize("{normal}") == "OK"


def test_default_callback_with_resolver_returning_none():
    def always_none_resolver(_args: list[str]) -> None:
        return None

    factory = ExpressionFactory([("key", always_none_resolver)])
    assert factory.materialize("{key:arg}") == "{key:arg}"


def test_custom_callback_context_aware():
    def context_callback(key: str, args: list[str]) -> str:
        if key == "env":
            return f"$ENV:{args[0] if args else 'UNKNOWN'}"
        if key == "var":
            return f"${args[0] if args else 'VAR'}"
        return f"{{{key}}}"

    factory = ExpressionFactory([], context_callback)
    assert factory.materialize("{env:PATH}") == "$ENV:PATH"
    assert factory.materialize("{var:name}") == "$name"
    assert factory.materialize("{other}") == "{other}"

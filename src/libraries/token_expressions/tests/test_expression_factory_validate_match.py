from ps.token_expressions import (
    ExpressionFactory,
    ExpressionSyntaxError,
)


def test_validate_match_valid_simple():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 and 1")
    assert result.success is True


def test_validate_match_valid_complex():
    factory = ExpressionFactory([])
    result = factory.validate_match("(1 and 1) or (0 and 1)")
    assert result.success is True


def test_validate_match_unbalanced_parentheses_unclosed():
    factory = ExpressionFactory([])
    result = factory.validate_match("(1 and 1")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)
    assert "unclosed" in result.errors[0].message.lower()


def test_validate_match_unbalanced_parentheses_extra_closing():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 and 1)")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)
    assert "unmatched" in result.errors[0].message.lower()


def test_validate_match_duplicate_operators():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 and and 1")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)


def test_validate_match_duplicate_operands():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 1 or 0")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)


def test_validate_match_operator_at_end():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 and")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)


def test_validate_match_operator_at_start():
    factory = ExpressionFactory([])
    result = factory.validate_match("and 1")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)


def test_validate_match_not_operator_valid():
    factory = ExpressionFactory([])
    result = factory.validate_match("not 0")
    assert result.success is True


def test_validate_match_not_in_sequence():
    factory = ExpressionFactory([])
    result = factory.validate_match("not not 1")
    assert result.success is True


def test_validate_match_empty_parentheses():
    factory = ExpressionFactory([])
    result = factory.validate_match("()")
    assert result.success is False
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], ExpressionSyntaxError)


def test_validate_match_with_tokens():
    def flag_resolver(_args: list[str]) -> str:
        return "1"

    factory = ExpressionFactory([("flag", flag_resolver)])
    result = factory.validate_match("{flag} and 1")
    assert result.success is True


def test_validate_match_with_unresolved_token():
    factory = ExpressionFactory([])
    result = factory.validate_match("{missing} and 1")
    assert result.success is False
    # Should fail on missing token, not syntax


def test_validate_match_valid_parentheses():
    factory = ExpressionFactory([])
    result = factory.validate_match("((1 and 1) or (0 and 1))")
    assert result.success is True


def test_validate_match_nested_not():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 and not (0 or 1)")
    assert result.success is True


def test_validate_match_operator_after_closing_paren():
    factory = ExpressionFactory([])
    result = factory.validate_match("(1) 1")
    assert result.success is False


def test_validate_match_multiple_errors():
    factory = ExpressionFactory([])
    # This might only catch the first error
    result = factory.validate_match("1 and and")
    assert result.success is False


def test_validate_match_complex_valid():
    factory = ExpressionFactory([])
    result = factory.validate_match("(1 and 1) or (not 0 and (1 or 0))")
    assert result.success is True


def test_validate_match_or_at_start():
    factory = ExpressionFactory([])
    result = factory.validate_match("or 1 and 1")
    assert result.success is False


def test_validate_match_paren_after_operand():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 (and 1)")
    assert result.success is False


def test_validate_match_valid_true_false():
    factory = ExpressionFactory([])
    result = factory.validate_match("True and False")
    assert result.success is True


def test_validate_match_empty_expression():
    factory = ExpressionFactory([])
    result = factory.validate_match("")
    assert result.success is True


def test_validate_match_whitespace_only():
    factory = ExpressionFactory([])
    result = factory.validate_match("   ")
    assert result.success is True


def test_validate_match_not_after_operand():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 not 0")
    assert result.success is False


def test_validate_match_valid_single_value():
    factory = ExpressionFactory([])
    result = factory.validate_match("1")
    assert result.success is True


def test_validate_match_valid_single_not():
    factory = ExpressionFactory([])
    result = factory.validate_match("not 1")
    assert result.success is True


def test_validate_match_valid_with_quotes():
    factory = ExpressionFactory([])
    result = factory.validate_match("'hello' and 'world'")
    assert result.success is True


def test_validate_match_nested_operators():
    factory = ExpressionFactory([])
    result = factory.validate_match("1 and 1 or 1 and 1")
    assert result.success is True


def test_validate_match_multiple_not():
    factory = ExpressionFactory([])
    result = factory.validate_match("not not not 1")
    assert result.success is True

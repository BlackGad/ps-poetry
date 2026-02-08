from typing import Callable, Optional

from ps.token_expressions import ExpressionFactory


def test_match_true_literal():
    factory = ExpressionFactory([])
    assert factory.match("true") is True


def test_match_false_literal():
    factory = ExpressionFactory([])
    assert factory.match("false") is True  # "false" is non-empty string


def test_match_zero_is_false():
    factory = ExpressionFactory([])
    assert factory.match("0") is False


def test_match_positive_number_is_true():
    factory = ExpressionFactory([])
    assert factory.match("1") is True
    assert factory.match("23") is True


def test_match_empty_string_is_false():
    factory = ExpressionFactory([])
    assert factory.match("") is False


def test_match_quoted_string_is_true():
    factory = ExpressionFactory([])
    assert factory.match("'some'") is True


def test_match_empty_quoted_string_is_false():
    factory = ExpressionFactory([])
    assert factory.match("''") is False


def test_match_and_operator():
    factory = ExpressionFactory([])
    assert factory.match("1 and 1") is True
    assert factory.match("1 and 0") is False
    assert factory.match("0 and 1") is False


def test_match_or_operator():
    factory = ExpressionFactory([])
    assert factory.match("1 or 0") is True
    assert factory.match("0 or 1") is True
    assert factory.match("0 or 0") is False


def test_match_not_operator():
    factory = ExpressionFactory([])
    assert factory.match("not 0") is True
    assert factory.match("not 1") is False


def test_match_parentheses():
    factory = ExpressionFactory([])
    assert factory.match("(1 and 1)") is True
    assert factory.match("(1 or 0)") is True


def test_match_complex_expression():
    factory = ExpressionFactory([])
    assert factory.match("(1 and 'some' or (1 or 23)) and not 0") is True


def test_match_with_tokens():
    def resolver_func(_args: list[str]) -> Optional[str]:
        return "1"

    factory = ExpressionFactory([("flag", resolver_func)])
    assert factory.match("{flag} and 1") is True


def test_match_with_tokens_and_fallback():
    factory = ExpressionFactory([])
    assert factory.match("{missing<1>} and 1") is True
    assert factory.match("{missing<0>} or 1") is True


def test_match_token_resolves_to_and_operator():
    def resolver(_args: list[str]) -> str:
        return "and"

    factory = ExpressionFactory([("op", resolver)])
    assert factory.match("1 {op} 1") is True
    assert factory.match("1 {op} 0") is False
    assert factory.match("0 {op} 1") is False
    assert factory.match("0 {op} 0") is False


def test_match_token_resolves_to_or_operator():
    def resolver(_args: list[str]) -> str:
        return "or"

    factory = ExpressionFactory([("op", resolver)])
    assert factory.match("1 {op} 1") is True
    assert factory.match("1 {op} 0") is True
    assert factory.match("0 {op} 1") is True
    assert factory.match("0 {op} 0") is False


def test_match_token_resolves_to_not_operator():
    def resolver(_args: list[str]) -> str:
        return "not"

    factory = ExpressionFactory([("op", resolver)])
    assert factory.match("{op} 0") is True
    assert factory.match("{op} 1") is False
    assert factory.match("{op} {op} 1") is True  # not not 1 = 1


def test_match_token_resolves_to_left_parenthesis():
    def resolver(_args: list[str]) -> str:
        return "("

    factory = ExpressionFactory([("paren", resolver)])
    assert factory.match("{paren}1 and 1)") is True
    assert factory.match("{paren}1 or 0) and 1") is True


def test_match_token_resolves_to_right_parenthesis():
    def resolver(_args: list[str]) -> str:
        return ")"

    factory = ExpressionFactory([("paren", resolver)])
    assert factory.match("(1 and 1{paren}") is True
    assert factory.match("(1 or 0{paren} and 1") is True


def test_match_token_resolves_to_both_parentheses():
    def left_resolver(_args: list[str]) -> str:
        return "("

    def right_resolver(_args: list[str]) -> str:
        return ")"

    factory = ExpressionFactory([("lp", left_resolver), ("rp", right_resolver)])
    assert factory.match("{lp}1 and 1{rp}") is True
    assert factory.match("{lp}1 or 0{rp} and 1") is True
    assert factory.match("not {lp}0 or 0{rp}") is True


def test_match_multiple_operator_tokens():
    def resolver(args: list[str]) -> str:
        return args[0] if args else "and"

    factory = ExpressionFactory([("op", resolver)])
    assert factory.match("1 {op:and} 1") is True
    assert factory.match("0 {op:or} 1") is True
    assert factory.match("{op:not} 0") is True


def test_match_complex_expression_with_operator_tokens():
    def op_resolver(args: list[str]) -> str:
        ops = {"a": "and", "o": "or", "n": "not"}
        return ops.get(args[0], "and") if args else "and"

    def paren_resolver(args: list[str]) -> str:
        return "(" if args and args[0] == "l" else ")"

    factory = ExpressionFactory([("op", op_resolver), ("p", paren_resolver)])

    # (1 and 1) or (not 0)
    assert factory.match("{p:l}1 {op:a} 1{p:r} {op:o} {p:l}{op:n} 0{p:r}") is True

    # (1 or 0) and (not 0)
    assert factory.match("{p:l}1 {op:o} 0{p:r} {op:a} {p:l}{op:n} 0{p:r}") is True

    # (0 and 0) or (not 1)
    assert factory.match("{p:l}0 {op:a} 0{p:r} {op:o} {p:l}{op:n} 1{p:r}") is False


def test_match_operator_token_preserves_boolean_logic():
    def and_resolver(_args: list[str]) -> str:
        return "and"

    def or_resolver(_args: list[str]) -> str:
        return "or"

    factory = ExpressionFactory([("and_op", and_resolver), ("or_op", or_resolver)])

    # Truth table for AND
    assert factory.match("1 {and_op} 1") is True
    assert factory.match("1 {and_op} 0") is False
    assert factory.match("0 {and_op} 1") is False
    assert factory.match("0 {and_op} 0") is False

    # Truth table for OR
    assert factory.match("1 {or_op} 1") is True
    assert factory.match("1 {or_op} 0") is True
    assert factory.match("0 {or_op} 1") is True
    assert factory.match("0 {or_op} 0") is False

    # Combined
    assert factory.match("1 {and_op} 1 {or_op} 0") is True
    assert factory.match("0 {or_op} 0 {and_op} 1") is False


def test_match_operator_tokens_with_values():
    def joint_resolver(args: list[str]) -> str:
        # Returns operator or value based on argument
        return args[0] if args else "1"

    factory = ExpressionFactory([("v", joint_resolver)])

    # Mix of value tokens and operator tokens
    assert factory.match("{v:1} {v:and} {v:1}") is True
    assert factory.match("{v:0} {v:or} {v:1}") is True
    assert factory.match("{v:not} {v:0}") is True


def test_match_nested_operator_tokens():
    def resolver(args: list[str]) -> str:
        mapping = {
            "and": "and",
            "or": "or",
            "not": "not",
            "(": "(",
            ")": ")",
        }
        return mapping.get(args[0], "1") if args else "1"

    factory = ExpressionFactory([("t", resolver)])

    # ((1 and 1) or 0) and not 0
    assert factory.match(
        "{t:(}{t:(}1 {t:and} 1{t:)} {t:or} 0{t:)} {t:and} {t:not} 0"
    ) is True

    # (1 or (0 and 1)) and 1
    assert factory.match(
        "{t:(}1 {t:or} {t:(}0 {t:and} 1{t:)}{t:)} {t:and} 1"
    ) is True


def test_match_operator_token_edge_cases():
    def resolver(_args: list[str]) -> str:
        return "and"

    factory = ExpressionFactory([("op", resolver)])

    # Multiple operators in sequence
    assert factory.match("1 {op} 1 {op} 1") is True
    assert factory.match("1 {op} 1 {op} 0") is False

    # Operators with values
    assert factory.match("1 {op} (1 {op} 1)") is True


def test_match_all_operators_as_tokens():
    operators = {
        "and_op": "and",
        "or_op": "or",
        "not_op": "not",
        "lparen": "(",
        "rparen": ")",
    }

    def make_resolver(op: str) -> Callable[[list[str]], str]:
        def resolver(_args: list[str]) -> str:
            return op
        return resolver

    resolvers = [(key, make_resolver(op)) for key, op in operators.items()]
    factory = ExpressionFactory(resolvers)

    # Build: (1 and 1) or (not 0)
    expr = "{lparen}1 {and_op} 1{rparen} {or_op} {lparen}{not_op} 0{rparen}"
    assert factory.match(expr) is True

    # Build: (0 or 0) and (not 1)
    expr = "{lparen}0 {or_op} 0{rparen} {and_op} {lparen}{not_op} 1{rparen}"
    assert factory.match(expr) is False

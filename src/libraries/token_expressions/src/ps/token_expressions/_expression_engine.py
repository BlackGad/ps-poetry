from typing import Optional

from ._validation import ExpressionSyntaxError, TokenError, ValidationResult


def _check_balanced_parentheses(expr: str) -> Optional[ExpressionSyntaxError]:
    paren_count = 0
    for i, char in enumerate(expr):
        if char == "(":
            paren_count += 1
        elif char == ")":
            paren_count -= 1
            if paren_count < 0:
                return ExpressionSyntaxError(
                    token=expr,
                    position=i,
                    message=f"Unmatched closing parenthesis at position {i}",
                )
    if paren_count > 0:
        return ExpressionSyntaxError(
            token=expr,
            position=0,
            message=f"Unmatched opening parenthesis ({paren_count} unclosed)",
        )
    return None


def _validate_token_sequence(expr: str, tokens: list[str]) -> ValidationResult:
    errors: list[TokenError] = []
    comparison_operators = {"==", "!=", ">=", "<=", ">", "<"}
    operators = {"and", "or", "not", "in"} | comparison_operators
    binary_operators = {"and", "or", "in"} | comparison_operators
    previous: Optional[str] = None
    expect_operand = True

    for i, current in enumerate(tokens):
        if current == "(":
            if previous and previous not in operators and previous != "(":
                errors.append(ExpressionSyntaxError(
                    token=expr,
                    position=0,
                    message=f"Unexpected '(' after {previous} at token position {i}",
                ))
            expect_operand = True
        elif current == ")":
            if expect_operand and previous != ")":
                errors.append(ExpressionSyntaxError(
                    token=expr,
                    position=0,
                    message=f"Unexpected ')' at token position {i}, expected operand",
                ))
            expect_operand = False
        elif current == "not":
            if not expect_operand and previous != "(" and previous not in operators:
                errors.append(ExpressionSyntaxError(
                    token=expr,
                    position=0,
                    message=f"Unexpected 'not' at token position {i}, expected binary operator",
                ))
            expect_operand = True
        elif current in binary_operators:
            if expect_operand:
                errors.append(ExpressionSyntaxError(
                    token=expr,
                    position=0,
                    message=f"Unexpected operator '{current}' at token position {i}, expected operand",
                ))
            expect_operand = True
        else:
            if not expect_operand and previous not in operators:
                errors.append(ExpressionSyntaxError(
                    token=expr,
                    position=0,
                    message=f"Unexpected operand '{current}' at token position {i}, expected operator",
                ))
            expect_operand = False
        previous = current

    if expect_operand and previous not in {"(", ")"}:
        errors.append(ExpressionSyntaxError(
            token=expr,
            position=0,
            message="Expression ends unexpectedly, expected operand",
        ))

    return ValidationResult(errors=tuple(errors))


def _process_quoted_string(expr: str, i: int) -> tuple[str, int]:
    quote_char = expr[i]
    string_chars = [quote_char]
    i += 1
    while i < len(expr):
        char = expr[i]
        string_chars.append(char)
        if char == quote_char:
            i += 1
            break
        i += 1
    return "".join(string_chars), i


def _process_bracket_list(expr: str, i: int) -> tuple[str, int]:
    bracket_depth = 1
    list_chars = ["["]
    i += 1
    while i < len(expr) and bracket_depth > 0:
        char = expr[i]
        list_chars.append(char)
        if char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        i += 1
    return "".join(list_chars), i


def _tokenize_expression(expr: str) -> list[str]:
    tokens, chars = [], []
    operators = ("and", "or", "not", "in")
    i = 0

    def flush_word() -> None:
        if chars and (word := "".join(chars).strip()):
            if word in operators:
                tokens.append(word)
            elif word.lower() == "true":
                tokens.append("True")
            elif word.lower() == "false":
                tokens.append("False")
            else:
                tokens.append(word)
            chars.clear()

    while i < len(expr):
        char = expr[i]

        # Handle quoted strings
        if char in ('"', "'"):
            flush_word()
            string_token, i = _process_quoted_string(expr, i)
            tokens.append(string_token)
            continue

        # Handle lists
        if char == "[":
            flush_word()
            list_token, i = _process_bracket_list(expr, i)
            tokens.append(list_token)
            continue

        # Handle comparison operators
        if char in (">", "<", "=", "!"):
            flush_word()
            if i + 1 < len(expr) and (char + expr[i + 1]) in ("==", "!=", ">=", "<="):
                tokens.append(char + expr[i + 1])
                i += 2
                continue
            if char in (">", "<"):
                tokens.append(char)
            i += 1
            continue

        # Handle parentheses
        if char in ("(", ")"):
            flush_word()
            tokens.append(char)
        # Handle whitespace
        elif char in (" ", "\t"):
            flush_word()
        # Accumulate characters
        else:
            chars.append(char)

        i += 1

    flush_word()
    return tokens


def _evaluate_expression(expr: str) -> bool:
    if not (expr := expr.strip()):
        return False
    try:
        return bool(eval(" ".join(_tokenize_expression(expr)), {"__builtins__": {}}, {}))  # noqa: S307
    except Exception:
        return False

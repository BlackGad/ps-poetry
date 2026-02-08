import re
from typing import Any, Callable, Optional, Sequence, Tuple, Union

from .token_resolvers import pick_resolver
from .validation import (
    ExpressionSyntaxError,
    FallbackTokenError,
    MissingResolverError,
    TokenError,
    UnresolvedTokenError,
    ValidationResult,
)


TokenValue = Union[str, int, bool]
TokenResolver = Callable[[list[str]], Optional[TokenValue]]
TokenResolverEntry = Tuple[str, Union[TokenResolver, Any]]
DefaultCallback = Callable[[str, list[str]], TokenValue]

_TOKEN_PATTERN = re.compile(r"\{([^{}]+)\}")


class ExpressionFactory:
    def __init__(
        self,
        token_resolvers: Sequence[TokenResolverEntry],
        default_callback: Optional[DefaultCallback] = None,
        max_recursion_depth: int = 10,
    ) -> None:
        self._token_resolvers = []
        for key, resolver in token_resolvers:
            self._token_resolvers.append((key, pick_resolver(resolver)))
        self._default_callback = default_callback
        self._max_recursion_depth = max_recursion_depth

    def materialize(self, value: str) -> str:
        if not value:
            return value

        result = value
        for _ in range(self._max_recursion_depth):
            has_changes = False

            def resolve(match: re.Match[str]) -> str:
                nonlocal has_changes
                expression = match.group(1)

                fallback = ""
                has_fallback = False
                if expression.endswith(">") and "<" in expression:
                    last_open = expression.rfind("<")
                    if last_open > 0:
                        fallback = expression[last_open + 1:-1]
                        expression = expression[:last_open]
                        has_fallback = True

                parts = expression.split(":")
                key = parts[0]
                if not key:
                    return fallback if has_fallback else match.group(0)

                args = parts[1:]

                for resolver_key, resolver in self._token_resolvers:
                    if resolver_key != key:
                        continue
                    resolved = resolver(args)
                    if resolved is not None:
                        resolved_str = str(resolved)
                        if resolved_str != match.group(0):
                            has_changes = True
                        return resolved_str

                if has_fallback:
                    has_changes = True
                    return fallback
                if self._default_callback is not None:
                    resolved_str = str(self._default_callback(key, args))
                    if resolved_str != match.group(0):
                        has_changes = True
                    return resolved_str
                return match.group(0)

            result = _TOKEN_PATTERN.sub(resolve, result)
            if not has_changes:
                break

        return result

    def validate_materialize(self, value: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        if not value:
            return ValidationResult(errors=[])

        errors: list[TokenError] = []
        checked_values = set()

        def validate_recursive(val: str, depth: int = 0) -> None:
            if depth >= self._max_recursion_depth or val in checked_values:
                return

            checked_values.add(val)

            for match in _TOKEN_PATTERN.finditer(val):
                expression = match.group(1)
                position = match.start()
                token = match.group(0)

                has_fallback = False
                fallback = ""
                if expression.endswith(">") and "<" in expression:
                    last_open = expression.rfind("<")
                    if last_open > 0:
                        fallback = expression[last_open + 1:-1]
                        expression = expression[:last_open]
                        has_fallback = True

                parts = expression.split(":")
                key = parts[0]
                if not key:
                    continue

                args = parts[1:]

                resolver_found = False
                resolved = False
                resolved_value = None

                for resolver_key, resolver in self._token_resolvers:
                    if resolver_key != key:
                        continue
                    resolver_found = True
                    result = resolver(args)
                    if result is not None:
                        resolved = True
                        resolved_value = str(result)
                        break

                # Skip if token is resolved
                if resolved:
                    # Check if the resolved value contains more tokens
                    if resolved_value and _TOKEN_PATTERN.search(resolved_value):
                        validate_recursive(resolved_value, depth + 1)
                    continue

                # Skip if has fallback and we're not treating fallbacks as failures
                if has_fallback and not threat_fallback_as_failure:
                    # Still check if fallback contains tokens
                    if fallback and _TOKEN_PATTERN.search(fallback):
                        validate_recursive(fallback, depth + 1)
                    continue

                # Report errors
                if not resolver_found:
                    if has_fallback:
                        errors.append(FallbackTokenError(
                            token=token,
                            position=position,
                            key=key,
                            args=args,
                            fallback=fallback,
                        ))
                        # Check if fallback contains tokens
                        if fallback and _TOKEN_PATTERN.search(fallback):
                            validate_recursive(fallback, depth + 1)
                    else:
                        errors.append(MissingResolverError(
                            token=token,
                            position=position,
                            key=key,
                        ))
                else:  # resolver found but not resolved
                    if has_fallback:
                        errors.append(FallbackTokenError(
                            token=token,
                            position=position,
                            key=key,
                            args=args,
                            fallback=fallback,
                        ))
                        # Check if fallback contains tokens
                        if fallback and _TOKEN_PATTERN.search(fallback):
                            validate_recursive(fallback, depth + 1)
                    else:
                        errors.append(UnresolvedTokenError(
                            token=token,
                            position=position,
                            key=key,
                            args=args,
                        ))

        validate_recursive(value)
        return ValidationResult(errors=errors)

    def validate_match(self, condition: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        # First validate token resolution
        result = self.validate_materialize(condition, threat_fallback_as_failure)
        if not result.success:
            return result

        # Materialize the expression
        materialized = self.materialize(condition)
        errors: list[TokenError] = []

        # Check for balanced parentheses
        paren_count = 0
        for i, char in enumerate(materialized):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count < 0:
                    errors.append(ExpressionSyntaxError(
                        token=materialized,
                        position=i,
                        message=f"Unmatched closing parenthesis at position {i}",
                    ))
                    return ValidationResult(errors=errors)

        if paren_count > 0:
            errors.append(ExpressionSyntaxError(
                token=materialized,
                position=0,
                message=f"Unmatched opening parenthesis ({paren_count} unclosed)",
            ))
            return ValidationResult(errors=errors)

        # Tokenize and check for valid operator/operand sequences
        try:
            tokens = self._tokenize_expression(materialized)
        except Exception as e:
            errors.append(ExpressionSyntaxError(
                token=materialized,
                position=0,
                message=f"Failed to tokenize expression: {e}",
            ))
            return ValidationResult(errors=errors)

        if not tokens:
            return ValidationResult(errors=[])

        # Check for valid token sequences
        operators = {'and', 'or', 'not'}
        parentheses = {'(', ')'}

        prev_token = None
        expect_operand = True

        for i, token in enumerate(tokens):
            if token == '(':
                # Opening parenthesis can appear at start or after operator/opening paren
                if prev_token and prev_token not in operators and prev_token != '(':
                    errors.append(ExpressionSyntaxError(
                        token=materialized,
                        position=0,
                        message=f"Unexpected '(' after {prev_token} at token position {i}",
                    ))
                expect_operand = True
            elif token == ')':
                # Closing parenthesis must follow operand or closing paren
                if expect_operand and prev_token != ')':
                    errors.append(ExpressionSyntaxError(
                        token=materialized,
                        position=0,
                        message=f"Unexpected ')' at token position {i}, expected operand",
                    ))
                expect_operand = False
            elif token == 'not':
                # 'not' is a unary operator, so it can appear when expecting operand
                if not expect_operand and prev_token != '(' and prev_token not in operators:
                    errors.append(ExpressionSyntaxError(
                        token=materialized,
                        position=0,
                        message=f"Unexpected 'not' at token position {i}, expected binary operator",
                    ))
                expect_operand = True
            elif token in operators:  # 'and', 'or'
                # Binary operators must follow operand or closing paren
                if expect_operand:
                    errors.append(ExpressionSyntaxError(
                        token=materialized,
                        position=0,
                        message=f"Unexpected operator '{token}' at token position {i}, expected operand",
                    ))
                expect_operand = True
            else:
                # Operand (True, False, or other value)
                if not expect_operand and prev_token not in operators:
                    errors.append(ExpressionSyntaxError(
                        token=materialized,
                        position=0,
                        message=f"Unexpected operand '{token}' at token position {i}, expected operator",
                    ))
                expect_operand = False

            prev_token = token

        # Check if expression ends expecting operand
        if expect_operand and prev_token not in parentheses:
            errors.append(ExpressionSyntaxError(
                token=materialized,
                position=0,
                message="Expression ends unexpectedly, expected operand",
            ))

        return ValidationResult(errors=errors)

    def match(self, condition: str) -> bool:
        materialized = self.materialize(condition)
        return self._evaluate_expression(materialized)

    def _to_bool(self, value: str) -> bool:
        value = value.strip()
        if not value:
            return False

        try:
            return int(value) > 0
        except ValueError:
            pass

        try:
            return float(value) > 0
        except ValueError:
            pass

        if value[0] in ('"', "'") and value[-1] == value[0]:
            return len(value) > 2

        return True

    def _tokenize_expression(self, expr: str) -> list[str]:
        tokens = []
        chars = []

        for char in expr:
            if char == '(':
                if chars:
                    word = ''.join(chars).strip()
                    if word:
                        tokens.append(word if word in ('and', 'or', 'not') else str(self._to_bool(word)))
                    chars.clear()
                tokens.append('(')
            elif char == ')':
                if chars:
                    word = ''.join(chars).strip()
                    if word:
                        tokens.append(word if word in ('and', 'or', 'not') else str(self._to_bool(word)))
                    chars.clear()
                tokens.append(')')
            elif char in (' ', '\t'):
                if chars:
                    word = ''.join(chars).strip()
                    if word:
                        tokens.append(word if word in ('and', 'or', 'not') else str(self._to_bool(word)))
                    chars.clear()
            else:
                chars.append(char)

        if chars:
            word = ''.join(chars).strip()
            if word:
                tokens.append(word if word in ('and', 'or', 'not') else str(self._to_bool(word)))

        return tokens

    def _evaluate_expression(self, expr: str) -> bool:
        if not expr:
            return False

        expr = expr.strip()
        if not expr:
            return False

        tokens = self._tokenize_expression(expr)
        python_expr = ' '.join(tokens)

        try:
            result = eval(python_expr, {"__builtins__": {}}, {})  # noqa: S307
            return bool(result)
        except Exception:
            return False

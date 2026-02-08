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


def _parse_token(expression: str) -> Tuple[str, list[str], str, bool]:
    fallback, has_fallback = "", False
    if expression.endswith(">") and (last_open := expression.rfind("<")) > 0:
        fallback = expression[last_open + 1:-1]
        expression = expression[:last_open]
        has_fallback = True
    parts = expression.split(":")
    return parts[0], parts[1:], fallback, has_fallback


def _check_balanced_parentheses(expr: str) -> Optional[ExpressionSyntaxError]:
    paren_count = 0
    for i, char in enumerate(expr):
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
            if paren_count < 0:
                return ExpressionSyntaxError(
                    token=expr, position=i,
                    message=f"Unmatched closing parenthesis at position {i}"
                )
    if paren_count > 0:
        return ExpressionSyntaxError(
            token=expr, position=0,
            message=f"Unmatched opening parenthesis ({paren_count} unclosed)"
        )
    return None


def _validate_token_sequence(expr: str, tokens: list[str]) -> ValidationResult:
    errors: list[TokenError] = []
    operators, previous, expect_operand = {'and', 'or', 'not'}, None, True

    for i, current in enumerate(tokens):
        if current == '(':
            if previous and previous not in operators and previous != '(':
                errors.append(ExpressionSyntaxError(
                    token=expr, position=0,
                    message=f"Unexpected '(' after {previous} at token position {i}"
                ))
            expect_operand = True
        elif current == ')':
            if expect_operand and previous != ')':
                errors.append(ExpressionSyntaxError(
                    token=expr, position=0,
                    message=f"Unexpected ')' at token position {i}, expected operand"
                ))
            expect_operand = False
        elif current == 'not':
            if not expect_operand and previous != '(' and previous not in operators:
                errors.append(ExpressionSyntaxError(
                    token=expr, position=0,
                    message=f"Unexpected 'not' at token position {i}, expected binary operator"
                ))
            expect_operand = True
        elif current in operators:
            if expect_operand:
                errors.append(ExpressionSyntaxError(
                    token=expr, position=0,
                    message=f"Unexpected operator '{current}' at token position {i}, expected operand"
                ))
            expect_operand = True
        else:
            if not expect_operand and previous not in operators:
                errors.append(ExpressionSyntaxError(
                    token=expr, position=0,
                    message=f"Unexpected operand '{current}' at token position {i}, expected operator"
                ))
            expect_operand = False
        previous = current

    if expect_operand and previous not in {'(', ')'}:
        errors.append(ExpressionSyntaxError(
            token=expr, position=0,
            message="Expression ends unexpectedly, expected operand"
        ))

    return ValidationResult(errors=errors)


def _to_bool(value: str) -> bool:
    if not (value := value.strip()):
        return False
    try:
        return int(value) > 0
    except ValueError:
        try:
            return float(value) > 0
        except ValueError:
            return len(value) > 2 if value[0] in ('"', "'") and value[-1] == value[0] else True


def _tokenize_expression(expr: str) -> list[str]:
    tokens, chars = [], []
    operators = ('and', 'or', 'not')

    def flush_word() -> None:
        if chars and (word := ''.join(chars).strip()):
            tokens.append(word if word in operators else str(_to_bool(word)))
            chars.clear()

    for char in expr:
        if char in ('(', ')'):
            flush_word()
            tokens.append(char)
        elif char in (' ', '\t'):
            flush_word()
        else:
            chars.append(char)

    flush_word()
    return tokens


def _evaluate_expression(expr: str) -> bool:
    if not (expr := expr.strip()):
        return False
    try:
        return bool(eval(' '.join(_tokenize_expression(expr)), {"__builtins__": {}}, {}))  # noqa: S307
    except Exception:
        return False


class ExpressionFactory:
    def __init__(
        self,
        token_resolvers: Sequence[TokenResolverEntry],
        default_callback: Optional[DefaultCallback] = None,
        max_recursion_depth: int = 10,
    ) -> None:
        self._token_resolvers = [(key, pick_resolver(resolver)) for key, resolver in token_resolvers]
        self._default_callback = default_callback
        self._max_recursion_depth = max_recursion_depth

    def _resolve_token(self, key: str, args: list[str]) -> Optional[TokenValue]:
        for resolver_key, resolver in self._token_resolvers:
            if resolver_key == key and (resolved := resolver(args)) is not None:
                return resolved
        return None

    def materialize(self, value: str) -> str:
        if not value:
            return value

        result = value
        for _ in range(self._max_recursion_depth):
            has_changes = False

            def resolve(match: re.Match[str]) -> str:
                nonlocal has_changes
                key, args, fallback, has_fallback = _parse_token(match.group(1))
                if not key:
                    return fallback if has_fallback else match.group(0)

                if (resolved := self._resolve_token(key, args)) is not None:
                    resolved_str = str(resolved)
                    has_changes |= resolved_str != match.group(0)
                    return resolved_str

                if has_fallback:
                    has_changes = True
                    return fallback
                if self._default_callback:
                    resolved_str = str(self._default_callback(key, args))
                    has_changes |= resolved_str != match.group(0)
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
        checked = set()

        def validate(val: str, depth: int = 0) -> None:
            if depth >= self._max_recursion_depth or val in checked:
                return
            checked.add(val)

            for match in _TOKEN_PATTERN.finditer(val):
                token, position = match.group(0), match.start()
                key, args, fallback, has_fallback = _parse_token(match.group(1))
                if not key:
                    continue

                resolved = self._resolve_token(key, args)
                if resolved is not None:
                    if _TOKEN_PATTERN.search(resolved_str := str(resolved)):
                        validate(resolved_str, depth + 1)
                    continue

                if has_fallback and not threat_fallback_as_failure:
                    if _TOKEN_PATTERN.search(fallback):
                        validate(fallback, depth + 1)
                    continue

                resolver_exists = any(rk == key for rk, _ in self._token_resolvers)
                if has_fallback:
                    errors.append(FallbackTokenError(token=token, position=position, key=key, args=args, fallback=fallback))
                    if _TOKEN_PATTERN.search(fallback):
                        validate(fallback, depth + 1)
                elif resolver_exists:
                    errors.append(UnresolvedTokenError(token=token, position=position, key=key, args=args))
                else:
                    errors.append(MissingResolverError(token=token, position=position, key=key))

        validate(value)
        return ValidationResult(errors=errors)

    def validate_match(self, condition: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        if not (result := self.validate_materialize(condition, threat_fallback_as_failure)).success:
            return result

        materialized = self.materialize(condition)

        if error := _check_balanced_parentheses(materialized):
            return ValidationResult(errors=[error])

        try:
            tokens = _tokenize_expression(materialized)
        except Exception as e:
            return ValidationResult(errors=[ExpressionSyntaxError(
                token=materialized, position=0,
                message=f"Failed to tokenize expression: {e}"
            )])

        if not tokens:
            return ValidationResult(errors=[])

        return _validate_token_sequence(materialized, tokens)

    def match(self, condition: str) -> bool:
        return _evaluate_expression(self.materialize(condition))

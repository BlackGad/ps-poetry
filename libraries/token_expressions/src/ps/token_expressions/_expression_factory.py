import re
from typing import Any, Callable, Optional, Sequence, Tuple, Union

from .token_resolvers import BaseResolver
from ._expression_engine import (
    _check_balanced_parentheses,
    _evaluate_expression,
    _tokenize_expression,
    _validate_token_sequence,
)
from ._validation import (
    ExpressionSyntaxError,
    FallbackTokenError,
    FallbackUsedWarning,
    MissingResolverError,
    TokenError,
    UnresolvedTokenError,
    ValidationResult,
    ValidationWarning,
)


TokenValue = Union[str, int, bool, list[Union[str, int, bool]]]
TokenResolver = Callable[[list[str]], Optional[TokenValue]]
RawFuncResolver = Callable[[str], Optional[TokenValue]]
TokenResolverEntry = Tuple[str, Union[RawFuncResolver, Any]]
DefaultCallback = Callable[[str, list[str]], TokenValue]

_TOKEN_PATTERN = re.compile(r"\{([^{}]+)\}")

_KEYWORDS = {"and", "or", "not", "in", "True", "False", "(", ")"}


def _is_numeric_string(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _token_value_to_str(value: TokenValue, for_eval: bool = False) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(repr(item) for item in value) + "]"
    if isinstance(value, str) and for_eval and value not in _KEYWORDS and not _is_numeric_string(value):
        return repr(value)
    return str(value)


def _parse_token(expression: str) -> Tuple[str, list[str], str, bool]:
    fallback, has_fallback = "", False
    if expression.endswith(">") and (last_open := expression.rfind("<")) > 0:
        fallback = expression[last_open + 1:-1]
        expression = expression[:last_open]
        has_fallback = True
    parts = expression.split(":")
    return parts[0], parts[1:], fallback, has_fallback


class ExpressionFactory:
    def __init__(
        self,
        token_resolvers: Sequence[TokenResolverEntry],
        default_callback: Optional[DefaultCallback] = None,
        max_recursion_depth: int = 10,
    ) -> None:
        self._token_resolvers = [(key, BaseResolver.pick_resolver(resolver)) for key, resolver in token_resolvers]
        self._default_callback = default_callback
        self._max_recursion_depth = max_recursion_depth

    def _resolve_token(self, key: str, args: list[str]) -> Optional[TokenValue]:
        for resolver_key, resolver in self._token_resolvers:
            if resolver_key == key and (resolved := resolver(args)) is not None:
                return resolved
        return None

    def materialize(self, value: str, for_eval: bool = False) -> str:
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
                    resolved_str = _token_value_to_str(resolved, for_eval=for_eval)
                    has_changes |= resolved_str != match.group(0)
                    return resolved_str

                if has_fallback:
                    has_changes = True
                    return fallback
                if self._default_callback:
                    resolved_str = _token_value_to_str(self._default_callback(key, args), for_eval=for_eval)
                    has_changes |= resolved_str != match.group(0)
                    return resolved_str
                return match.group(0)

            result = _TOKEN_PATTERN.sub(resolve, result)
            if not has_changes:
                break
        return result

    def validate_materialize(self, value: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        if not value:
            return ValidationResult(errors=())

        errors: list[TokenError] = []
        warnings: list[ValidationWarning] = []
        checked: set[str] = set()

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
                    if _TOKEN_PATTERN.search(resolved_str := _token_value_to_str(resolved, for_eval=False)):
                        validate(resolved_str, depth + 1)
                    continue

                resolver_exists = any(rk == key for rk, _ in self._token_resolvers)
                if has_fallback and not threat_fallback_as_failure:
                    underlying_error: TokenError = (
                        UnresolvedTokenError(token=token, position=position, key=key, args=args)
                        if resolver_exists
                        else MissingResolverError(token=token, position=position, key=key)
                    )
                    warnings.append(FallbackUsedWarning(error=underlying_error, fallback=fallback))
                    if _TOKEN_PATTERN.search(fallback):
                        validate(fallback, depth + 1)
                    continue

                if has_fallback:
                    errors.append(FallbackTokenError(token=token, position=position, key=key, args=args, fallback=fallback))
                    if _TOKEN_PATTERN.search(fallback):
                        validate(fallback, depth + 1)
                elif resolver_exists:
                    errors.append(UnresolvedTokenError(token=token, position=position, key=key, args=args))
                else:
                    errors.append(MissingResolverError(token=token, position=position, key=key))

        validate(value)
        return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))

    def validate_match(self, condition: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        if not (result := self.validate_materialize(condition, threat_fallback_as_failure)).success:
            return result

        materialized = self.materialize(condition)

        if error := _check_balanced_parentheses(materialized):
            return ValidationResult(errors=(error,))

        try:
            tokens = _tokenize_expression(materialized)
        except Exception as e:
            return ValidationResult(errors=(ExpressionSyntaxError(
                token=materialized,
                position=0,
                message=f"Failed to tokenize expression: {e}",
            ),))

        if not tokens:
            return ValidationResult(errors=())

        return _validate_token_sequence(materialized, tokens)

    def match(self, condition: str) -> bool:
        return _evaluate_expression(self.materialize(condition, for_eval=True))

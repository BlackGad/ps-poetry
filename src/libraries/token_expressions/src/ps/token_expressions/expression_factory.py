import re
from typing import Any, Callable, Optional, Sequence, Tuple, Union

from .token_resolvers import pick_resolver


TokenValue = Union[str, int, bool]
TokenResolver = Callable[[list[str]], Optional[TokenValue]]
TokenResolverEntry = Tuple[str, Union[TokenResolver, Any]]

_TOKEN_PATTERN = re.compile(r"\{([^{}]+)\}")


class ExpressionFactory:
    def __init__(self, token_resolvers: Sequence[TokenResolverEntry]) -> None:
        self._token_resolvers = []
        for key, resolver in token_resolvers:
            self._token_resolvers.append((key, pick_resolver(resolver)))

    def materialize(self, value: str) -> str:
        if not value:
            return value

        def resolve(match: re.Match[str]) -> str:
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
                    return str(resolved)

            return fallback if has_fallback else match.group(0)

        return _TOKEN_PATTERN.sub(resolve, value)

    def match(self, condition: str) -> bool:
        materialized = self.materialize(condition)
        return self._evaluate_expression(materialized)

    def _to_bool(self, value: str) -> bool:
        value = value.strip()
        if not value:
            return False

        try:
            num = int(value)
            return num > 0
        except ValueError:
            pass

        try:
            num = float(value)
            return num > 0
        except ValueError:
            pass

        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return len(value) > 2

        return True

    def _tokenize_expression(self, expr: str) -> list[str]:
        tokens = []
        current = ""
        i = 0
        while i < len(expr):
            char = expr[i]

            if char == '(':
                if current.strip():
                    tokens.append(str(self._to_bool(current)))
                    current = ""
                tokens.append('(')
            elif char == ')':
                if current.strip():
                    tokens.append(str(self._to_bool(current)))
                    current = ""
                tokens.append(')')
            elif char in (' ', '\t'):
                if current.strip():
                    word = current.strip()
                    if word in ('and', 'or', 'not'):
                        tokens.append(word)
                    else:
                        tokens.append(str(self._to_bool(word)))
                    current = ""
            else:
                current += char

            i += 1

        if current.strip():
            word = current.strip()
            if word in ('and', 'or', 'not'):
                tokens.append(word)
            else:
                tokens.append(str(self._to_bool(word)))

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

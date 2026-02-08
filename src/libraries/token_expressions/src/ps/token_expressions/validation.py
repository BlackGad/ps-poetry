from dataclasses import dataclass


@dataclass(frozen=True)
class TokenError:
    token: str
    position: int


@dataclass(frozen=True)
class MissingResolverError(TokenError):
    key: str


@dataclass(frozen=True)
class UnresolvedTokenError(TokenError):
    key: str
    args: list[str]


@dataclass(frozen=True)
class FallbackTokenError(TokenError):
    key: str
    args: list[str]
    fallback: str


@dataclass(frozen=True)
class ExpressionSyntaxError(TokenError):
    message: str


@dataclass
class ValidationResult:
    errors: list[TokenError]

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def __bool__(self) -> bool:
        return self.success

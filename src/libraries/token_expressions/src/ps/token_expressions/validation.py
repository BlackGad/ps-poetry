from dataclasses import dataclass


@dataclass(frozen=True)
class TokenError:
    token: str
    position: int

    def __str__(self) -> str:
        return f"Token '{self.token}' at position {self.position}"


@dataclass(frozen=True)
class MissingResolverError(TokenError):
    key: str

    def __str__(self) -> str:
        return f"Missing resolver for key '{self.key}' in token '{self.token}' at position {self.position}"


@dataclass(frozen=True)
class UnresolvedTokenError(TokenError):
    key: str
    args: list[str]

    def __str__(self) -> str:
        args_str = ", ".join(self.args)
        return f"Unresolved token '{self.key}({args_str})' in '{self.token}' at position {self.position}"


@dataclass(frozen=True)
class FallbackTokenError(TokenError):
    key: str
    args: list[str]
    fallback: str

    def __str__(self) -> str:
        args_str = ", ".join(self.args)
        return f"Token '{self.key}({args_str})' in '{self.token}' at position {self.position} fell back to '{self.fallback}'"


@dataclass(frozen=True)
class ExpressionSyntaxError(TokenError):
    message: str

    def __str__(self) -> str:
        return f"Syntax error in '{self.token}' at position {self.position}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[TokenError]

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def __bool__(self) -> bool:
        return self.success

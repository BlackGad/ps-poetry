# PS Token Expressions

A flexible token-based expression resolution and materialization library for Python.

This library enables dynamic string templating through token substitution and conditional evaluation. It supports multiple resolver types, nested access patterns, fallback values, and boolean expression matching.

## Overview

PS Token Expressions provides:

* **Token materialization** — Replace `{tokens}` in strings with dynamic values
* **Conditional matching** — Evaluate boolean expressions with tokens using logical and comparison operators
* **Membership testing** — Use `in` and `not in` operators with lists and strings
* **Token validation** — Detect and report all resolution issues
* **Multiple resolver types** — Dict, function, instance, and custom resolver support
* **Nested access** — Navigate through nested data structures
* **Fallback values** — Provide defaults when tokens cannot be resolved
* **Type-safe** — Returns strings, integers, booleans, or lists

## Installation

```bash
pip install ps-token-expressions
```

Or with Poetry:

```bash
poetry add ps-token-expressions
```

## Quick Start

```python
import os

from ps.token_expressions import ExpressionFactory

factory = ExpressionFactory([
    ("config", {"version": "1.2.3", "build": 456}),
    ("env", lambda arg: os.getenv(arg) if arg else None),
    ("tags", ["production", "release", "stable"]),
])

result = factory.materialize("{config:version}")
# Output: "1.2.3"

if factory.match("{config:build} and {env:CI}"):
    print("Running in CI with build number")

if factory.match("'production' in {tags}"):
    print("Production release detected")
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-token-expressions/basic_usage_example.py)

## Core Concepts

### Token Format

Tokens are enclosed in curly braces and follow this format:

```txt
{key:arg1:arg2:...<fallback>}
```

Components:

* **key** — Identifies the resolver
* **args** — Colon-separated arguments passed to the resolver
* **fallback** — Optional default value when resolution fails

### Materialization

Replace tokens in a string with resolved values:

```python
factory = ExpressionFactory([("app", {"name": "MyApp"})])
result = factory.materialize("Application: {app:name}")
# Output: "Application: MyApp"
```

### Conditional Matching

Evaluate boolean expressions containing tokens:

```python
factory = ExpressionFactory([("flag", True)])
if factory.match("{flag} and 1"):
    print("Condition met")
```

## Creating an ExpressionFactory

Create a factory with resolvers that provide values for tokens:

```python
from ps.token_expressions import ExpressionFactory

resolvers = [
    ("config", {"version": "1.2.3"}),  # Dict resolver
    ("env", lambda arg: os.getenv(arg)),  # Function resolver
]

factory = ExpressionFactory(resolvers)
```

Each resolver is a `(key, source)` tuple where:

* **key** identifies the resolver (used in `{key:...}`)
* **source** can be a dict, function, list, or object

### Default Callback

Provide a callback for unresolved tokens (optional):

```python
def handle_missing(key: str, args: list[str]) -> str:
    return f"MISSING:{key}"

factory = ExpressionFactory(resolvers, default_callback=handle_missing)
factory.materialize("{unknown}")  # "MISSING:unknown"
```

**When the callback is NOT used:**

* Token is successfully resolved
* Fallback value is provided

```python
factory.materialize("{missing<fallback>}")  # "fallback" (callback not called)
```

## Resolver Types

Resolvers provide values for tokens. The library supports four types:

### Dict Resolver

Use dictionaries to provide configuration data:

```python
config = {"version": "1.2.3", "app": {"name": "MyApp"}}
factory = ExpressionFactory([("config", config)])

factory.materialize("{config:version}")      # "1.2.3"
factory.materialize("{config:app:name}")     # "MyApp" (nested access)
```

### List Resolver

Access list elements by index:

```python
items = ["alpha", "beta", "gamma"]
factory = ExpressionFactory([("items", items)])

factory.materialize("{items:0}")   # "alpha"
factory.materialize("{items:1}")   # "beta"
```

Lists of primitive values (strings, integers, booleans) can be used directly with the `in` operator:

```python
numbers = [1, 2, 3, 4, 5]
factory = ExpressionFactory([("nums", numbers)])

factory.match("3 in {nums}")       # True
factory.match("6 not in {nums}")   # True
```

Works with nested lists and lists containing dicts or objects.

### Function Resolver

Call functions to generate values dynamically:

```python
def get_env(arg: str) -> str:
    return os.getenv(arg) if arg else ""

factory = ExpressionFactory([("env", get_env)])
factory.materialize("{env:PATH}")   # Returns PATH value
```

### Instance Resolver

Access object attributes:

```python
class Config:
    version = "2.0.0"
    debug = True

factory = ExpressionFactory([("app", Config())])
factory.materialize("{app:version}")   # "2.0.0"
factory.materialize("{app:debug}")     # "True"
```

Objects can be callable, have nested attributes, or contain dicts/lists.

### Custom Resolver

Implement a custom resolver by subclassing `BaseResolver`. The resolver receives the full `args` list from the token — for example, `{key:arg1:arg2}` passes `["arg1", "arg2"]`. Use `BaseResolver.pick_resolver()` to obtain a resolver for an intermediate value and delegate remaining args to it.

```python
from typing import Optional

from ps.token_expressions import BaseResolver, ExpressionFactory


class RegistryResolver(BaseResolver):
    def __init__(self, data: dict) -> None:
        self._data = data

    def __call__(self, args: list[str]) -> Optional[str]:
        if not args:
            return None
        value = self._data.get(args[0])
        if value is None:
            return None
        if len(args) > 1:
            sub = BaseResolver.pick_resolver(value)
            result = sub(args[1:])
            return str(result) if result is not None else None
        return str(value)


registry = {
    "config": {"host": "prod.example.com", "port": 443},
    "version": "2.5.0",
}

factory = ExpressionFactory([("reg", RegistryResolver(registry))])
factory.materialize("{reg:version}")       # "2.5.0"
factory.materialize("{reg:config:host}")   # "prod.example.com"
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-token-expressions/custom_resolver_example.py)

## Fallback Values

Provide default values when tokens can't be resolved using `<fallback>` syntax:

```python
factory = ExpressionFactory([])

factory.materialize("{missing<default>}")   # "default"
factory.materialize("{missing<0>}")         # "0"
factory.materialize("{missing<>}")          # ""
```

**Resolution priority:**

1. Resolved value (if successful)
2. Fallback value (if provided)
3. Default callback or original token

```python
data = {"version": "1.2.3"}
factory = ExpressionFactory([("app", data)])

factory.materialize("{app:version<0.0.0>}")   # "1.2.3" (resolved)
factory.materialize("{app:missing<0.0.0>}")   # "0.0.0" (fallback)
factory.materialize("{app:missing}")          # "{app:missing}" (no fallback)
```

## Nested Access

Navigate through nested data structures using colon-separated paths:

```python
# Nested dicts
config = {"database": {"host": "localhost", "port": 5432}}
factory = ExpressionFactory([("cfg", config)])
factory.materialize("{cfg:database:host}")  # "localhost"

# Objects with dicts
class App:
    settings = {"debug": True}

factory = ExpressionFactory([("app", App())])
factory.materialize("{app:settings:debug}")  # "True"

# Lists with dicts
servers = [{"name": "prod", "url": "prod.com"}, {"name": "dev"}]
factory = ExpressionFactory([("srv", servers)])
factory.materialize("{srv:0:name}")  # "prod"
```

## Boolean Expressions

Evaluate boolean expressions with token substitution using `and`, `or`, `not`, `in`, and comparison operators. Values follow Python truthiness rules (empty strings and `0` are falsy).

```python
factory = ExpressionFactory([("config", {"enabled": True})])

factory.match("1 and 1")                               # True
factory.match("{config:enabled} and 1")                # True
factory.match("{config:missing<0>} or 1")              # True
```

### Comparison Operators

Compare values using `==`, `!=`, `>`, `<`, `>=`, and `<=`. Operators work with or without surrounding spaces:

```python
factory = ExpressionFactory([("ver", lambda _: "2")])

factory.match("2 > 1")                    # True
factory.match("1 == 1")                   # True
factory.match("1 != 0")                   # True
factory.match("2 >= 2")                   # True
factory.match("1 <= 2")                   # True

# With token values
factory.match("{ver} >= 1")               # True
factory.match("{ver} == 2")               # True

# Operators can be written without spaces
factory.match("2>1")                      # True
factory.match("1==1")                     # True

# Combined with logical operators
factory.match("2 > 1 and 3 > 2")         # True
factory.match("(1 == 1) or (2 != 3)")    # True
```

### Membership Testing with `in` Operator

Test if values are present in lists or strings:

```python
# Test membership in lists
items = [1, 2, 3]
factory = ExpressionFactory([("items", items)])

factory.match("1 in {items}")                          # True
factory.match("4 in {items}")                          # False
factory.match("4 not in {items}")                      # True

# Test substring containment in strings
text = "hello world"
factory = ExpressionFactory([("text", text)])

factory.match("'hello' in {text}")                     # True
factory.match("'xyz' not in {text}")                   # True

# Use with literal lists
factory.match("1 in [1, 2, 3]")                        # True
factory.match("'a' in ['a', 'b', 'c']")                # True

# Combine with other operators
factory.match("1 in {items} and 'h' in {text}")        # True
factory.match("4 not in {items} or 2 in {items}")      # True
```

## Recursive Token Resolution

Resolver output can contain tokens that will be resolved automatically up to `max_recursion_depth` (default: 10). Useful for configuration chains and template indirection.

```python
def env_name(_arg: str) -> str:
    return "production"

def db_config(arg: str) -> str:
    return "{db_host:" + arg + "}"

def db_host(arg: str) -> str:
    hosts = {"production": "prod.db.com", "dev": "localhost"}
    return hosts.get(arg, "localhost")

factory = ExpressionFactory([
    ("env", env_name),
    ("config", db_config),
    ("db_host", db_host),
])

result = factory.materialize("Connecting to: {config:{env}}")
# Output: "Connecting to: prod.db.com"
# Resolution: {env} -> "production" -> {db_host:production} -> "prod.db.com"
```

## Nested Token Arguments

A token can be used as an argument to another token by placing it inside the outer token's argument position: `{outer:{inner}}`. The innermost tokens are resolved first; their values are then substituted as arguments for the outer token.

```python
config = {"production": "prod.example.com", "staging": "stg.example.com"}
factory = ExpressionFactory([
    ("server", config),
    ("env", lambda _: "production"),
])

factory.materialize("{server:{env}}")   # "prod.example.com"
# Resolution: {env} -> "production", then {server:production} -> "prod.example.com"
```

Nested tokens can appear anywhere within the argument list. Static args and dynamic token args can be mixed freely:

```python
factory = ExpressionFactory([
    ("join", JoinResolver()),   # BaseResolver returning "-".join(args)
    ("val", lambda _: "mid"),
])

factory.materialize("{join:a:{val}:b}")   # "a-mid-b"
# Resolution: {val} -> "mid", then {join:a:mid:b} -> "a-mid-b"
```

Nesting can go multiple levels deep. Tokens are resolved from the innermost outward:

```python
factory = ExpressionFactory([
    ("a", lambda arg: f"a({arg})"),
    ("b", lambda arg: f"b({arg})"),
    ("c", lambda _: "leaf"),
])

factory.materialize("{a:{b:{c}}}")   # "a(b(leaf))"
# Resolution: {c} -> "leaf", then {b:leaf} -> "b(leaf)", then {a:b(leaf)} -> "a(b(leaf))"
```

When using function resolvers (plain functions or lambdas), the resolver receives the first argument as a single `str`. When multiple arguments or access to the full argument list is required, use a `BaseResolver` subclass instead:

```python
from typing import Optional

from ps.token_expressions import BaseResolver, ExpressionFactory


class JoinResolver(BaseResolver):
    def __call__(self, args: list[str]) -> Optional[str]:
        return "-".join(args)


factory = ExpressionFactory([
    ("join", JoinResolver()),
    ("year", lambda _: "2026"),
    ("month", lambda _: "03"),
])

factory.materialize("{join:{year}:{month}}")   # "2026-03"
```

If the inner token cannot be resolved, the outer token is also left unresolved:

```python
factory = ExpressionFactory([("outer", lambda arg: f"got:{arg}")])
factory.materialize("{outer:{missing}}")   # "{outer:{missing}}"
```

## Token Validation

Check template validity before using them with `validate_materialize()`. Returns a `ValidationResult` with a `success` property, an `errors` list, and a `warnings` list — without raising exceptions.

```python
template = "Version: {app:version}, Build: {ci:build}"
result = factory.validate_materialize(template)

if result.success:
    output = factory.materialize(template)
else:
    for error in result.errors:
        print(f"Error at position {error.position}: {error.token}")
```

When a token cannot be resolved but a fallback value is available, validation still succeeds. A `FallbackUsedWarning` is added to `result.warnings` containing the original error and the fallback value that was used:

```python
factory = ExpressionFactory([])
result = factory.validate_materialize("{missing<default>}")

assert result.success  # True — fallback keeps it valid
for warning in result.warnings:
    print(warning)  # Fallback value 'default' was used: Missing resolver for key 'missing' ...
```

Passing `threat_fallback_as_failure=True` treats fallback usage as an error instead, adding a `FallbackTokenError` to `result.errors` and producing no warnings.

Error types: `MissingResolverError` (no resolver registered), `UnresolvedTokenError` (resolver returned `None`), `FallbackTokenError` (fallback used when `threat_fallback_as_failure=True`), `ExpressionSyntaxError` (invalid boolean expression syntax).

## Type Conversion

Resolved values are automatically converted to strings during materialization (numbers, booleans, etc.). Lists of primitive values (strings, integers, booleans) are formatted as Python list literals for use in conditional expressions with the `in` operator.

```python
# List resolver returns list for use in conditions
items = [1, 2, 3]
factory = ExpressionFactory([("items", items)])

# In conditions, lists are formatted as [1, 2, 3]
factory.match("1 in {items}")                          # True

# In materialization, returns string representation
factory.materialize("{items}")                         # "[1, 2, 3]"
```

## Advanced Features

Custom default callbacks handle unresolved tokens (useful for logging or converting unknown tokens to environment-style references):

```python
def env_callback(key: str, args: list[str]) -> str:
    if key == "env":
        return f"$ENV:{args[0] if args else 'UNKNOWN'}"
    return f"{{{key}}}"

factory = ExpressionFactory([], env_callback)
factory.materialize("{env:PATH}")              # "$ENV:PATH"
factory.materialize("{unknown}")               # "{unknown}"
```

## Complete Example

A complete working example combining instance resolvers, function resolvers, token materialization, fallback values, membership testing, and boolean conditions.

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-token-expressions/basic_usage_example.py)

## Error Handling

Errors are handled gracefully - unresolved tokens return original text, resolver exceptions are caught and treated as `None`, triggering fallback values if provided.

```python
factory = ExpressionFactory([])
result = factory.materialize("{missing:token<fallback>}")
# Output: "fallback"
```

## Best Practices

* Use meaningful resolver keys
* Provide fallbacks for critical values
* Keep resolver functions simple
* Use type hints for maintainability

## API Reference

### ExpressionFactory

```python
ExpressionFactory(
    token_resolvers: Sequence[Tuple[str, Any]],
    default_callback: Optional[Callable[[str, list[str]], TokenValue]] = None,
    max_recursion_depth: int = 10
)
```

Methods:

* `materialize(value: str) -> str` - Replace tokens with resolved values
* `match(condition: str) -> bool` - Evaluate boolean expression
* `validate_materialize(value: str, threat_fallback_as_failure: bool = False) -> ValidationResult` - Validate tokens without exceptions
* `validate_match(condition: str, threat_fallback_as_failure: bool = False) -> ValidationResult` - Validate boolean expression and tokens

### BaseResolver

Abstract base class for implementing custom token resolvers.

```python
class BaseResolver(ABC):
    def __call__(self, args: list[str]) -> Optional[TokenValue]: ...

    @staticmethod
    def resolve_factory(source: Any) -> Optional[TokenResolver]: ...

    @classmethod
    def register_resolvers(cls, factories: Iterable[ResolverFactory]) -> None: ...

    @classmethod
    def pick_resolver(cls, source: Any) -> TokenResolver: ...
```

Subclass `BaseResolver` and implement `__call__` to receive the full `args` list from the token. Call `BaseResolver.pick_resolver(value)` to obtain a resolver for an intermediate value and delegate remaining args to it.

To register custom resolver factories, call `BaseResolver.register_resolvers(factories)` with an iterable of `ResolverFactory` callables. Each factory receives a source value and returns a `TokenResolver` or `None` if it cannot handle that source type. Registered factories are consulted in registration order.

### ValidationResult

```python
@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[TokenError, ...]
    warnings: tuple[ValidationWarning, ...]
```

### Error Types

```python
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
```

### Warning Types

```python
@dataclass(frozen=True)
class ValidationWarning:
    pass

@dataclass(frozen=True)
class FallbackUsedWarning(ValidationWarning):
    error: TokenError
    fallback: str
```

`FallbackUsedWarning` is added to `ValidationResult.warnings` whenever a token cannot be resolved but a fallback value is present and `threat_fallback_as_failure=False`. The `error` field contains the underlying `MissingResolverError` or `UnresolvedTokenError` that would have been raised otherwise.

### Type Signatures

Function resolver signature: `(arg: str) -> Optional[str | int | bool | list[str | int | bool]]`

Default callback signature: `(key: str, args: list[str]) -> str | int | bool | list[str | int | bool]`

**Note:** Resolvers can return lists of primitive values (strings, integers, booleans) for use with the `in` operator in conditional expressions.

## Summary

PS Token Expressions is a lightweight library for dynamic string templating with token substitution.

**What it does:**

* Replace tokens in strings with dynamic values
* Evaluate conditional expressions with tokens
* Test membership with `in` and `not in` operators
* Validate templates before using them
* Navigate nested data structures
* Provide fallback values for missing data

**Why use it:**

* **Simple** — No template language to learn, just `{token}` syntax
* **Flexible** — Works with dicts, functions, objects, and lists
* **Safe** — Validates templates without exceptions
* **Extensible** — Create custom resolvers easily

**Perfect for:**

* Configuration templates
* Dynamic version strings
* Build scripts and CI/CD
* Feature flags and conditionals
* Tag and category filtering
* Path generation

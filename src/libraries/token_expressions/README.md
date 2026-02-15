# PS Token Expressions

A flexible token-based expression resolution and materialization library for Python.

This library enables dynamic string templating through token substitution and conditional evaluation. It supports multiple resolver types, nested access patterns, fallback values, and boolean expression matching.

## Overview

PS Token Expressions provides:

* **Token materialization** — Replace `{tokens}` in strings with dynamic values
* **Conditional matching** — Evaluate boolean expressions with tokens
* **Membership testing** — Use `in` and `not in` operators with lists and strings
* **Token validation** — Detect and report all resolution issues
* **Multiple resolver types** — Dict, function, and instance-based resolution
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
from ps.token_expressions import ExpressionFactory

# Define token resolvers
resolvers = [
    ("config", {"version": "1.2.3", "build": 456}),
    ("env", lambda args: os.getenv(args[0]) if args else None),
    ("tags", ["production", "release", "stable"]),
]

# Create factory
factory = ExpressionFactory(resolvers)

# Materialize tokens
result = factory.materialize("{config:version}")
# Output: "1.2.3"

# Match conditions
if factory.match("{config:build} and {env:CI}"):
    print("Running in CI with build number")

# Test membership
if factory.match("'production' in {tags}"):
    print("Production release detected")
```

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
    ("env", lambda args: os.getenv(args[0])),  # Function resolver
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
def get_env(args: list[str]) -> str:
    return os.getenv(args[0]) if args else ""

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

---

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

---

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

---

## Conditional Matching

Evaluate boolean expressions with token substitution using `and`, `or`, `not`, `in` operators and parentheses. Values follow Python truthiness rules (empty strings and `0` are falsy).

```python
factory = ExpressionFactory([("config", {"enabled": True})])

factory.match("1 and 1")                               # True
factory.match("{config:enabled} and 1")                # True
factory.match("{config:missing<0>} or 1")              # True
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
def env_name(_args: list[str]) -> str:
    return "production"

def db_config(args: list[str]) -> str:
    return "{db_host:" + args[0] + "}"

def db_host(args: list[str]) -> str:
    hosts = {"production": "prod.db.com", "dev": "localhost"}
    return hosts.get(args[0], "localhost")

factory = ExpressionFactory([
    ("env", env_name),
    ("config", db_config),
    ("db_host", db_host),
])

result = factory.materialize("Connecting to: {config:{env}}")
# Output: "Connecting to: prod.db.com"
# Resolution: {env} -> "production" -> {db_host:production} -> "prod.db.com"
```

## Token Validation

Check template validity before using them with `validate_materialize()`. Returns a `ValidationResult` with `success` property and `errors` list, without raising exceptions.

```python
template = "Version: {app:version}, Build: {ci:build}"
result = factory.validate_materialize(template)

if result.success:
    output = factory.materialize(template)
else:
    for error in result.errors:
        print(f"Error at position {error.position}: {error.token}")
```

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

```python
import os
from ps.token_expressions import ExpressionFactory

class AppConfig:
    def __init__(self):
        self.name = "MyApp"
        self.version = "1.0.0"
        self.tags = ["production", "stable"]

def env_resolver(args: list[str]) -> str | None:
    return os.getenv(args[0]) if args else None

factory = ExpressionFactory([
    ("app", AppConfig()),
    ("env", env_resolver),
])

# Build connection string
conn_str = factory.materialize("App: {app:name} v{app:version}")

# Check environment flag
if factory.match("{env:DEBUG<0>}"):
    print("Debug mode enabled")

# Check if running in production
if factory.match("'production' in {app:tags}"):
    print("Running in production mode")

# Check multiple conditions
if factory.match("'stable' in {app:tags} and not {env:DEBUG<0>}"):
    print("Stable production build")
```

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

### ValidationResult

```python
@dataclass
class ValidationResult:
    errors: list[TokenError]
    
    @property
    def success(self) -> bool
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

### Resolver Types

Function signature: `(args: list[str]) -> Optional[str | int | bool | list[str | int | bool]]`

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

# PS Token Expressions

A flexible token-based expression resolution and materialization library for Python.

This library enables dynamic string templating through token substitution and conditional evaluation. It supports multiple resolver types, nested access patterns, fallback values, and boolean expression matching.

## 1. Overview

PS Token Expressions provides:

* **Token materialization** — Replace `{tokens}` in strings with dynamic values
* **Conditional matching** — Evaluate boolean expressions with tokens
* **Token validation** — Detect and report all resolution issues
* **Multiple resolver types** — Dict, function, and instance-based resolution
* **Nested access** — Navigate through nested data structures
* **Fallback values** — Provide defaults when tokens cannot be resolved
* **Type-safe** — Returns strings, integers, or booleans

## 2. Installation

```bash
pip install ps-token-expressions
```

Or with Poetry:

```bash
poetry add ps-token-expressions
```

## 3. Quick Start

```python
from ps.token_expressions import ExpressionFactory

# Define token resolvers
resolvers = [
    ("config", {"version": "1.2.3", "build": 456}),
    ("env", lambda args: os.getenv(args[0]) if args else None),
]

# Create factory
factory = ExpressionFactory(resolvers)

# Materialize tokens
result = factory.materialize("{config:version}")
# Output: "1.2.3"

# Match conditions
if factory.match("{config:build} and {env:CI}"):
    print("Running in CI with build number")
```

## 4. Core Concepts

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

## 5. Creating an ExpressionFactory

The `ExpressionFactory` accepts a sequence of resolver entries and an optional default callback:

```python
from ps.token_expressions import ExpressionFactory

resolvers = [
    ("key1", resolver1),
    ("key2", resolver2),
    # ... more resolvers
]

factory = ExpressionFactory(resolvers)

# Or with custom default callback
factory = ExpressionFactory(resolvers, default_callback=my_callback)
```

Each resolver entry is a tuple of `(key, source)` where:

* **key** — Token identifier (first part of `{key:...}`)
* **source** — Dict, function, or object instance

### Default Callback

The default callback is invoked when a token cannot be resolved and no fallback is provided. It receives the key and arguments and must return a value.

**Signature:**

```python
from typing import Union

TokenValue = Union[str, int, bool]

def default_callback(key: str, args: list[str]) -> TokenValue:
    # Return a value for unresolved tokens
    pass
```

**Default behavior** (if no callback provided):

Returns the original token unchanged:

```python
factory = ExpressionFactory([])
factory.materialize("{missing}")           # "{missing}"
factory.materialize("{missing:arg1:arg2}") # "{missing:arg1:arg2}"
```

**Custom callback:**

```python
def custom_callback(key: str, args: list[str]) -> str:
    return f"UNRESOLVED:{key}"

factory = ExpressionFactory([], custom_callback)
factory.materialize("{missing}")           # "UNRESOLVED:missing"
factory.materialize("{foo:bar}")           # "UNRESOLVED:foo"
```

**Callback is NOT called when:**

* Token is successfully resolved
* Fallback value is provided

```python
def callback(key: str, args: list[str]) -> str:
    return "CALLBACK"

factory = ExpressionFactory([], callback)

# Fallback is used, callback NOT called
factory.materialize("{missing<fallback>}") # "fallback"
```

## 6. Resolver Types

### Dict Resolver

Resolves tokens by dictionary key lookup:

```python
data = {
    "version": "1.2.3",
    "app": {
        "name": "MyApp",
        "port": 8080
    }
}

factory = ExpressionFactory([("config", data)])

factory.materialize("{config:version}")        # "1.2.3"
factory.materialize("{config:app:name}")       # "MyApp"
factory.materialize("{config:app:port}")       # "8080"
```

**Features:**

* Nested dictionary access
* Type conversion (int/bool → string)
* Returns `None` for missing keys

### Function Resolver

Resolves tokens by calling a function with arguments:

```python
def env_resolver(args: list[str]) -> str | None:
    if args:
        return os.getenv(args[0])
    return None

factory = ExpressionFactory([("env", env_resolver)])

factory.materialize("{env:PATH}")              # Returns PATH value
factory.materialize("{env:MISSING<default>}")  # "default"
```

**Function signature:**

```python
def resolver(args: list[str]) -> str | int | bool | None:
    # args[0] is first argument after key
    # Return None if cannot resolve
    pass
```

### Instance Resolver

Resolves tokens by accessing object attributes:

```python
class Config:
    def __init__(self):
        self.version = "2.0.0"
        self.debug = True
        self.server = ServerConfig()

class ServerConfig:
    def __init__(self):
        self.port = 3000

config = Config()
factory = ExpressionFactory([("app", config)])

factory.materialize("{app:version}")           # "2.0.0"
factory.materialize("{app:debug}")             # "True"
factory.materialize("{app:server:port}")       # "3000"
```

**Features:**

* Nested attribute access
* Optional `confirm_resolve(args, value)` method for validation
* Falls back to calling object if callable

### Callable Instance Resolver

If an instance is callable, it acts as a function resolver:

```python
class CustomResolver:
    def __call__(self, args: list[str]) -> str | None:
        if args and args[0] == "custom":
            return "custom_value"
        return None

factory = ExpressionFactory([("cr", CustomResolver())])
factory.materialize("{cr:custom}")             # "custom_value"
```

### Mixed Resolvers

Combine dict, instance, and function resolvers:

```python
class AppConfig:
    def __init__(self):
        self.settings = {"debug": True}

def random_resolver(args: list[str]) -> str:
    return str(random.randint(1, 100))

factory = ExpressionFactory([
    ("app", AppConfig()),
    ("rand", random_resolver),
    ("env", os.environ),
])

factory.materialize("{app:settings:debug}")    # "True"
factory.materialize("{rand:num}")              # "42" (random)
factory.materialize("{env:USER}")              # Current user
```

## 7. Fallback Values

Fallbacks provide default values when resolution fails:

### Syntax

```txt
{key:arg<fallback>}
```

### Examples

```python
factory = ExpressionFactory([])

# String fallback
factory.materialize("{missing<default>}")      # "default"

# Numeric fallback
factory.materialize("{missing<0>}")            # "0"
factory.materialize("{missing<42>}")           # "42"

# Empty fallback
factory.materialize("{missing<>}")             # ""

# String literal fallback
factory.materialize("{missing<'1.0.0'>}")      # "'1.0.0'"

# Boolean fallback
factory.materialize("{missing<true>}")         # "true"
```

### Fallback Priority

1. Resolved value (if successful)
2. Fallback value (if provided)
3. Original token (if no fallback)

```python
data = {"version": "1.2.3"}
factory = ExpressionFactory([("app", data)])

# Resolved - uses actual value
factory.materialize("{app:version<0.0.0>}")    # "1.2.3"

# Not resolved - uses fallback
factory.materialize("{app:missing<0.0.0>}")    # "0.0.0"

# Not resolved - no fallback
factory.materialize("{app:missing}")           # "{app:missing}"
```

## 8. Nested Access

All resolver types support nested access:

### Nested Dictionaries

```python
data = {
    "level1": {
        "level2": {
            "level3": {
                "value": "deep"
            }
        }
    }
}

factory = ExpressionFactory([("config", data)])
factory.materialize("{config:level1:level2:level3:value}")  # "deep"
```

### Mixed Dict and Instance

```python
class Server:
    def __init__(self):
        self.port = 3000

data = {"server": Server()}
factory = ExpressionFactory([("config", data)])
factory.materialize("{config:server:port}")    # "3000"
```

### Instance with Dict Attribute

```python
class Config:
    def __init__(self):
        self.settings = {"debug": True, "port": 8080}

factory = ExpressionFactory([("app", Config())])
factory.materialize("{app:settings:debug}")    # "True"
factory.materialize("{app:settings:port}")     # "8080"
```

## 9. Conditional Matching

Evaluate boolean expressions with token substitution:

### Basic Operators

```python
factory = ExpressionFactory([])

# Logical operators
factory.match("1 and 1")                       # True
factory.match("1 or 0")                        # True
factory.match("not 0")                         # True

# Parentheses
factory.match("(1 and 1) or 0")                # True
```

### Truthiness Rules

| Value          | Result |
| -------------- | ------ |
| `0`            | False  |
| Positive int   | True   |
| Empty string   | False  |
| Non-empty      | True   |
| `''` or `""`   | False  |
| `'text'`       | True   |

### With Tokens

```python
def flag_resolver(args: list[str]) -> bool:
    return True

factory = ExpressionFactory([("flag", flag_resolver)])

factory.match("{flag} and 1")                  # True
factory.match("{flag} or 0")                   # True
factory.match("not {flag}")                    # False
```

### Complex Conditions

```python
data = {"enabled": True, "count": 5}
factory = ExpressionFactory([("config", data)])

# (enabled and count) means both exist and are truthy
factory.match("{config:enabled} and {config:count}")  # True

# With fallback
factory.match("{config:missing<1>} and 1")     # True
```

## 10. Recursive Token Resolution

When a resolver returns a value containing tokens, those tokens are automatically resolved up to `max_recursion_depth` (default: 10).

### Basic Recursion

```python
def get_template(_args: list[str]) -> str:
    return "{value}"

def get_value(_args: list[str]) -> str:
    return "final"

factory = ExpressionFactory([
    ("template", get_template),
    ("value", get_value),
])

result = factory.materialize("{template}")
# Output: "final"
# Resolution: {template} -> {value} -> final
```

### Multi-Level Recursion

```python
def level1(_args: list[str]) -> str:
    return "{level2}"

def level2(_args: list[str]) -> str:
    return "{level3}"

def level3(_args: list[str]) -> str:
    return "resolved"

factory = ExpressionFactory([
    ("level1", level1),
    ("level2", level2),
    ("level3", level3),
])

result = factory.materialize("{level1}")
# Output: "resolved"
```

### Controlling Recursion Depth

```python
def recursive(_args: list[str]) -> str:
    return "{recursive}"

factory = ExpressionFactory(
    [("recursive", recursive)],
    max_recursion_depth=5
)

result = factory.materialize("{recursive}")
# Stops after 5 iterations, returns "{recursive}"
```

### Recursive Validation

The `validate_materialize` method checks tokens at all recursion levels:

```python
def level1(_args: list[str]) -> str:
    return "{level2}"

def level2(_args: list[str]) -> str:
    return "{missing}"  # This will be detected!

factory = ExpressionFactory([
    ("level1", level1),
    ("level2", level2),
])

result = factory.validate_materialize("{level1}")
# result.success == False
# Detects missing resolver at nested level
```

### Practical Use Cases

**Configuration chains:**

```python
def env_name(_args: list[str]) -> str:
    return "production"

def db_config(args: list[str]) -> str:
    env = args[0] if args else "dev"
    return "{db_host:" + env + "}"

def db_host(args: list[str]) -> str:
    hosts = {"production": "prod.db.com", "dev": "localhost"}
    return hosts.get(args[0], "unknown") if args else "localhost"

factory = ExpressionFactory([
    ("env", env_name),
    ("config", db_config),
    ("db_host", db_host),
])

result = factory.materialize("Connecting to: {config:{env}}")
# Output: "Connecting to: prod.db.com"
```

## 11. Token Validation

The `validate_materialize` method checks all tokens in a string and returns detailed error information without raising exceptions.

### ValidationResult

The validation result includes:

* **`success` property** - `True` if no errors found
* **`errors` list** - All detected issues
* **Boolean conversion** - Can be used directly in conditions

```python
from ps.token_expressions import ExpressionFactory

factory = ExpressionFactory([("config", {"version": "1.0.0"})])

result = factory.validate_materialize("{config:version} {missing}")
if not result.success:
    for error in result.errors:
        print(f"Error at position {error.position}: {error.token}")
```

### Error Types

**MissingResolverError**

No resolver registered for the token key:

```python
factory = ExpressionFactory([])
result = factory.validate_materialize("{unknown:arg}")

error = result.errors[0]
# error.key == "unknown"
# error.token == "{unknown:arg}"
# error.position == 0
```

**UnresolvedTokenError**

Resolver exists but returned `None` (and no fallback provided):

```python
def resolver(_args: list[str]) -> None:
    return None

factory = ExpressionFactory([("key", resolver)])
result = factory.validate_materialize("{key:arg}")

error = result.errors[0]
# error.key == "key"
# error.args == ["arg"]
# error.token == "{key:arg}"
```

**FallbackTokenError**

Token has a fallback value but resolver didn't resolve (only when `threat_fallback_as_failure=True`):

```python
factory = ExpressionFactory([])
result = factory.validate_materialize("{missing<fallback>}", threat_fallback_as_failure=True)

error = result.errors[0]
# error.key == "missing"
# error.args == []
# error.fallback == "fallback"
# error.token == "{missing<fallback>}"
```

### Common Use Cases

**Pre-validation before materialization:**

```python
template = "Version: {app:version}, Build: {ci:build}"
result = factory.validate_materialize(template)

if result.success:
    output = factory.materialize(template)
else:
    print("Template has errors:")
    for error in result.errors:
        print(f"  - {error}")
```

**Configuration validation:**

```python
config_templates = {
    "greeting": "Hello, {user:name}!",
    "footer": "{app:name} v{app:version}",
}

for name, template in config_templates.items():
    result = factory.validate_materialize(template)
    if not result.success:
        print(f"Invalid template '{name}':")
        for error in result.errors:
            print(f"  Position {error.position}: {error.token}")
```

**Detecting missing dependencies:**

```python
from ps.token_expressions import MissingResolverError

result = factory.validate_materialize(template)
missing_keys = {
    error.key 
    for error in result.errors 
    if isinstance(error, MissingResolverError)
}

if missing_keys:
    print(f"Missing resolvers: {', '.join(missing_keys)}")
```

### Validation Behavior

**Tokens with fallbacks are valid by default:**

```python
result = factory.validate_materialize("{missing<default>}")
assert result.success is True  # Fallback provided, treated as valid
```

**Strict validation with `threat_fallback_as_failure`:**

```python
result = factory.validate_materialize("{missing<default>}", threat_fallback_as_failure=True)
assert result.success is False  # Fallback tokens reported as errors
assert isinstance(result.errors[0], FallbackTokenError)
```

This is useful when you want to ensure all tokens resolve properly, even if fallbacks are present.

**Empty keys are ignored:**

```python
result = factory.validate_materialize("{:arg}")
assert result.success is True  # Empty key skipped
```

**All errors are collected:**

```python
result = factory.validate_materialize("{a} {b} {c}")
# Returns all errors, not just the first one
assert len(result.errors) == 3
```

**Position tracking:**

```python
result = factory.validate_materialize("text {first} more {second}")
assert result.errors[0].position == 5   # Start of {first}
assert result.errors[1].position == 19  # Start of {second}
```

### Boolean Expression Validation

The `validate_match` method validates both token resolution AND boolean expression syntax:

```python
factory = ExpressionFactory([("flag", lambda _: "1")])

# Valid expression
result = factory.validate_match("{flag} and 1")
assert result.success is True

# Invalid: unbalanced parentheses
result = factory.validate_match("(1 and 1")
assert result.success is False
assert isinstance(result.errors[0], ExpressionSyntaxError)

# Invalid: duplicate operators
result = factory.validate_match("1 and and 1")
assert result.success is False

# Invalid: duplicate operands
result = factory.validate_match("1 1 or 0")
assert result.success is False

# Invalid: operator at end
result = factory.validate_match("1 and")
assert result.success is False
```

### ExpressionSyntaxError

Returned when boolean expression has structural issues:

```python
result = factory.validate_match("(1 and 1")
error = result.errors[0]
# error.token == "(1 and 1"
# error.position == 0
# error.message == "Unmatched opening parenthesis (1 unclosed)"
```

Common syntax errors detected:

* Unbalanced parentheses: `(1 and 1` or `1 and 1)`
* Duplicate operators: `1 and and 1`
* Duplicate operands: `1 1 or 0`
* Missing operands: `1 and` or `and 1`
* Invalid operator placement: `1 not 0` (not is unary)
* Empty expressions in parentheses: `()`

## 12. Type Conversion

All resolved values are converted to strings during materialization:

```python
data = {
    "string": "text",
    "number": 42,
    "boolean": True,
    "float": 3.14,
}

factory = ExpressionFactory([("data", data)])

factory.materialize("{data:string}")           # "text"
factory.materialize("{data:number}")           # "42"
factory.materialize("{data:boolean}")          # "True"
factory.materialize("{data:float}")            # "3.14"
```

## 13. Advanced Features

### Resolver Ordering

When multiple resolvers share the same key, the first match wins:

```python
def first_resolver(args: list[str]) -> None:
    return None

def second_resolver(args: list[str]) -> str:
    return "second"

factory = ExpressionFactory([
    ("key", first_resolver),
    ("key", second_resolver),
])

factory.materialize("{key:arg}")               # "second"
```

### Confirm Resolve Validation

Instance resolvers can validate resolved values:

```python
class ValidatedConfig:
    def __init__(self):
        self.version = "1.2.3"
    
    def confirm_resolve(self, args: list[str], value: str) -> bool:
        # Only allow version if it starts with "1."
        if args[0] == "version":
            return value.startswith("1.")
        return True

factory = ExpressionFactory([("config", ValidatedConfig())])
factory.materialize("{config:version}")        # "1.2.3"
```

If `confirm_resolve` returns `False`, the resolution fails and fallback is used.

### Custom Default Callbacks

Create context-aware default callbacks for unresolved tokens:

```python
def env_style_callback(key: str, args: list[str]) -> str:
    if key == "env":
        return f"$ENV:{args[0] if args else 'UNKNOWN'}"
    if key == "var":
        return f"${args[0] if args else 'VAR'}"
    return f"{{{key}}}"

factory = ExpressionFactory([], env_style_callback)

factory.materialize("{env:PATH}")          # "$ENV:PATH"
factory.materialize("{var:name}")          # "$name"
factory.materialize("{other}")             # "{other}"
```

### Logging Unresolved Tokens

```python
unresolved_tokens = []

def logging_callback(key: str, args: list[str]) -> str:
    unresolved_tokens.append((key, args))
    return f"{{{key}:{':'.join(args)}}}"

factory = ExpressionFactory(resolvers, logging_callback)
result = factory.materialize(template)

# Check what couldn't be resolved
for key, args in unresolved_tokens:
    print(f"Unresolved: {key} with args {args}")
```

## 14. Complete Examples

### Configuration Management

```python
import os
from ps.token_expressions import ExpressionFactory

class AppConfig:
    def __init__(self):
        self.name = "MyApp"
        self.version = "1.0.0"
        self.database = {
            "host": "localhost",
            "port": 5432
        }

def env_resolver(args: list[str]) -> str | None:
    return os.getenv(args[0]) if args else None

factory = ExpressionFactory([
    ("app", AppConfig()),
    ("env", env_resolver),
])

# Build connection string
conn_str = factory.materialize(
    "postgresql://{app:database:host}:{app:database:port}/{app:name}"
)
# Output: "postgresql://localhost:5432/MyApp"

# Check environment
if factory.match("{env:DEBUG<0>}"):
    print("Debug mode enabled")
```

### Template System

```python
def date_resolver(args: list[str]) -> str:
    from datetime import datetime
    if args:
        return datetime.now().strftime(f"%{args[0]}")
    return str(datetime.now())

factory = ExpressionFactory([
    ("date", date_resolver),
    ("config", {"app": "MyApp", "version": "2.0.0"}),
])

template = """
Application: {config:app}
Version: {config:version}
Built: {date:Y-%m-%d}
"""

result = factory.materialize(template)
```

### Dynamic Version Generation

```python
class GitInfo:
    def __init__(self):
        self.hash = "abc123"
        self.distance = 5
        self.dirty = False

class VersionBuilder:
    def __init__(self):
        self.spec = {"major": 1, "minor": 2, "patch": 3}
        self.git = GitInfo()

factory = ExpressionFactory([("v", VersionBuilder())])

# Clean build
version = factory.materialize(
    "{v:spec:major}.{v:spec:minor}.{v:spec:patch}+g{v:git:hash}"
)
# Output: "1.2.3+gabc123"

# With distance
if factory.match("{v:git:distance}"):
    version = factory.materialize(
        "{v:spec:major}.{v:spec:minor}.{v:spec:patch}"
        ".post{v:git:distance}+g{v:git:hash}"
    )
    # Output: "1.2.3.post5+gabc123"
```

## 15. Error Handling

The library handles errors gracefully:

### Missing Tokens

Tokens that cannot be resolved return the original token text (unless fallback is provided):

```python
factory = ExpressionFactory([])
result = factory.materialize("{missing:token}")
# Output: "{missing:token}"
```

### Invalid Arguments

Invalid arguments return `None` from resolvers, triggering fallback:

```python
def strict_resolver(args: list[str]) -> str | None:
    if args and args[0] == "valid":
        return "ok"
    return None

factory = ExpressionFactory([("strict", strict_resolver)])
result = factory.materialize("{strict:invalid<fallback>}")
# Output: "fallback"
```

### Exception Handling

Exceptions in resolvers are caught and treated as `None`:

```python
def error_resolver(args: list[str]) -> str:
    raise ValueError("Something went wrong")

factory = ExpressionFactory([("error", error_resolver)])
result = factory.materialize("{error:arg<safe>}")
# Output: "safe"
```

## 16. Best Practices

### Use Meaningful Keys

```python
# Good
factory = ExpressionFactory([
    ("env", os.environ),
    ("git", git_info),
    ("config", config),
])

# Avoid
factory = ExpressionFactory([
    ("a", os.environ),
    ("b", git_info),
    ("c", config),
])
```

### Provide Fallbacks for Critical Values

```python
# Good
version = factory.materialize("{git:version<0.0.0>}")

# Risky
version = factory.materialize("{git:version}")  # May return "{git:version}"
```

### Keep Resolvers Simple

```python
# Good
def simple_resolver(args: list[str]) -> str | None:
    if args:
        return lookup_value(args[0])
    return None

# Avoid complex logic
def complex_resolver(args: list[str]) -> str | None:
    # ... 50 lines of logic ...
    pass
```

### Use Typed Resolvers

```python
from typing import Optional

def typed_resolver(args: list[str]) -> Optional[str]:
    # Type hints improve maintainability
    return process(args) if args else None
```

## 17. API Reference

### ExpressionFactory

```python
class ExpressionFactory:
    def __init__(
        self, 
        token_resolvers: Sequence[Tuple[str, Any]],
        default_callback: Optional[Callable[[str, list[str]], TokenValue]] = None,
        max_recursion_depth: int = 10,
    ) -> None:
        """
        Create an expression factory.
        
        Args:
            token_resolvers: List of (key, resolver) tuples
            default_callback: Optional callback for unresolved tokens
                             Receives (key, args) and returns a value
                             Not called if fallback is provided
                             Default: None (returns original token)
            max_recursion_depth: Maximum depth for recursive token resolution
                               Default: 10
        """
    
    def materialize(self, value: str) -> str:
        """
        Replace tokens in string with resolved values.
        Supports recursive resolution up to max_recursion_depth.
        
        Args:
            value: String containing tokens
            
        Returns:
            String with tokens replaced
            
        Note:
            If a resolver returns a value containing tokens,
            those tokens will be resolved recursively.
        """
    
    def match(self, condition: str) -> bool:
        """
        Evaluate boolean expression with token substitution.
        
        Args:
            condition: Expression to evaluate
            
        Returns:
            True if condition evaluates to true
        """
    
    def validate_materialize(self, value: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        """
        Validate all tokens in string and collect errors.
        Checks tokens recursively up to max_recursion_depth.
        
        Args:
            value: String containing tokens to validate
            threat_fallback_as_failure: If True, tokens with fallbacks are reported as errors
            
        Returns:
            ValidationResult with success status and error list
            
        Note:
            - By default, tokens with fallbacks are valid
            - Does not raise exceptions
            - Collects all errors, not just the first
            - Validates recursively resolved tokens
        """
    
    def validate_match(self, condition: str, threat_fallback_as_failure: bool = False) -> ValidationResult:
        """
        Validate boolean expression structure and token resolution.
        
        Args:
            condition: Boolean expression to validate
            threat_fallback_as_failure: If True, tokens with fallbacks are reported as errors
            
        Returns:
            ValidationResult with success status and error list
            
        Note:
            - First validates token resolution (like validate_materialize)
            - Then validates boolean expression syntax:
              * Balanced parentheses
              * Valid operator/operand sequences
              * No duplicate operators or operands
        """
```

### ValidationResult

```python
from dataclasses import dataclass

@dataclass
class ValidationResult:
    errors: list[TokenError]
    
    @property
    def success(self) -> bool:
        """True if no errors found"""
        return len(self.errors) == 0
    
    def __bool__(self) -> bool:
        """Allow boolean conversion"""
        return self.success
```

### Error Types

```python
@dataclass(frozen=True)
class TokenError:
    token: str      # Full token text including braces
    position: int   # Character position in string

@dataclass(frozen=True)
class MissingResolverError(TokenError):
    key: str        # The resolver key that was not found

@dataclass(frozen=True)
class UnresolvedTokenError(TokenError):
    key: str        # The resolver key
    args: list[str] # Arguments passed to resolver

@dataclass(frozen=True)
class FallbackTokenError(TokenError):
    key: str        # The resolver key
    args: list[str] # Arguments passed to resolver
    fallback: str   # The fallback value

@dataclass(frozen=True)
class ExpressionSyntaxError(TokenError):
    message: str    # Description of the syntax error
```

### Default Callback Signature

```python
from typing import Union

TokenValue = Union[str, int, bool]

def default_callback(key: str, args: list[str]) -> TokenValue:
    """
    Handle unresolved tokens.
    
    Args:
        key: Token key (first part of {key:...})
        args: Token arguments (parts after key)
        
    Returns:
        Value to use for unresolved token
        
    Note:
        Not called if token is resolved or fallback is provided
    """
    pass
```

### Resolver Function Signature

```python
from typing import Optional, Union

TokenValue = Union[str, int, bool]

def resolver(args: list[str]) -> Optional[TokenValue]:
    """
    Resolve token arguments to a value.
    
    Args:
        args: Arguments from token (e.g., {key:arg1:arg2} → ["arg1", "arg2"])
        
    Returns:
        Resolved value or None if cannot resolve
    """
    pass
```

## 18. Comparison with Other Systems

| Feature                  | PS Token Expressions | String.format() | Jinja2 |
| ------------------------ | -------------------- | --------------- | ------ |
| Simple token replacement | ✓                    | ✓               | ✓      |
| Nested access            | ✓                    | ✗               | ✓      |
| Conditional matching     | ✓                    | ✗               | ✓      |
| Fallback values          | ✓                    | ✗               | ✓      |
| Custom resolvers         | ✓                    | ✗               | ~      |
| No template language     | ✓                    | ✓               | ✗      |
| Lightweight              | ✓                    | ✓               | ✗      |

PS Token Expressions provides a middle ground between simple formatting and full templating engines.

## 19. Summary

PS Token Expressions offers a flexible, lightweight solution for:

* **Dynamic string generation** with token substitution
* **Token validation** with detailed error reporting
* **Configuration management** with nested access
* **Conditional evaluation** with boolean expressions
* **Type-safe resolution** with fallback support

Key advantages:

* No template language to learn
* Type-safe and predictable
* Comprehensive validation without exceptions
* Extensible resolver system
* Graceful error handling
* Nested data structure support

Perfect for:

* Version string generation
* Configuration file templates  
* Template validation and diagnostics
* Dynamic path construction
* CI/CD pipeline logic
* Feature flag evaluation



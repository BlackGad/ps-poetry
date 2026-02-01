# Custom Version Pattern Specification

This plugin allows you to define how your package version is generated using declarative patterns.

A version is produced by evaluating a list of patterns. Each pattern may have an optional condition. The first matching pattern is used.

The system supports:

* SemVer, PEP 440, NuGet, CalVer, and hybrid versions
* Git-based versioning
* CI / environment variables
* Date- and random-based generation
* Safe defaults and fallbacks

---

## 1. Default Behavior

If no `patterns` configuration is provided, the following default sequence is used:

```txt
{in} -> {env:VERSION} -> {spec} -> 0.0.0
```

Meaning:

1. Use `--version` input if provided
2. Otherwise use `VERSION` environment variable
3. Otherwise use version from `pyproject.toml`
4. Otherwise fall back to `0.0.0`

---

## 2. Configuration

Define patterns in `pyproject.toml`:

```toml
[tool.poetry-version-pattern]
patterns = [
  "[git:dirty] {git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}.dirty",
  "[in] {in}",
  "[env:BUILD_NUMBER] {git:major}.{git:minor}.{git:patch}.post{git:distance}+ci.{env:BUILD_NUMBER}+g{git:hash}",
  "{spec}"
]
```

Patterns are evaluated top to bottom. The first matching entry wins.

---

## 3. Pattern Format

Each entry is either:

Unconditional:

```txt
<pattern>
```

Conditional:

```txt
[<condition>] <pattern>
```

Example:

```txt
[in:pep440] {in}
```

---

## 4. Tags in Patterns

Patterns may contain tags:

```txt
{expression}
```

An expression has the form:

```txt
source[:name][:modifier...][<fallback>]
```

---

## 5. Sources

| Source     | Description                     |
| ---------- | ------------------------------- |
| `spec`     | Version from pyproject.toml     |
| `in`       | Version from --version argument |
| `git`      | Selected Git tag                |
| `env:NAME` | Environment variable            |

Raw access:

If no modifier is given, the raw value is returned.

Examples:

```txt
{spec}
{in}
{git}
{env:VERSION}
```

---

## 6. Accessors (Value Modifiers)

### Core numbers

| Modifier | Meaning            | Default |
| -------- | ------------------ | ------- |
| `major`  | First number       | 0       |
| `minor`  | Second number      | 0       |
| `patch`  | Third number       | 0       |
| `rev`    | Fourth number      | 0       |
| `core`   | All numbers joined | 0       |

### Pre-release

| Modifier    | Meaning          | Default |
| ----------- | ---------------- | ------- |
| `pre`       | Full pre-release | ""      |
| `pre_label` | Label            | ""      |
| `pre_num`   | Number           | 0       |

### PEP 440

| Modifier | Meaning     | Default |
| -------- | ----------- | ------- |
| `dev`    | Dev number  | 0       |
| `post`   | Post number | 0       |

### Metadata

| Modifier | Meaning       | Default |
| -------- | ------------- | ------- |
| `meta`   | Full metadata | ""      |
| `meta0`  | First part    | ""      |
| `meta1`  | Second part   | ""      |

### Git-only

| Modifier   | Meaning           | Default |
| ---------- | ----------------- | ------- |
| `hash`     | Commit hash       | ""      |
| `distance` | Commits since tag | 0       |
| `dirty`    | Dirty flag        | false   |

### Classification

| Modifier   | Meaning         |
| ---------- | --------------- |
| `standard` | Detected format |

---

## 7. Generators

### Date

```txt
{date:<format>}
```

Uses C# DateTime formatting.

Examples:

```txt
{date:yyyy.MM.dd}
{date:yyMM}
{date:yyyyMMdd}
```

### Random

| Tag                 | Description     |
| ------------------- | --------------- |
| `rand:num`          | Random integer  |
| `rand:num:min..max` | Random in range |
| `rand:uuid`         | UUID v4         |
| `rand:hash`         | Short hash      |

Examples:

```txt
{rand:num}
{rand:uuid}
```

---

## 8. Fallback Values

Fallbacks use `< >`:

```txt
{in:minor<0>}
{env:VERSION<'1.0.0'>}
{git:hash<''>}
```

Used when:

* Source is missing
* Parsing fails
* Field is absent

Defaults when no fallback is provided:

| Type    | Default |
| ------- | ------- |
| Number  | 0       |
| String  | ""      |
| Boolean | false   |

---

## 9. Conditions

Conditions control which pattern is selected. They appear inside `[ ]`.

### Operators

```txt
and
or
not
( )
```

### Predicate functions

```txt
eq(a, b)
gt(a, b)
gte(a, b)
lt(a, b)
lte(a, b)
in(a, ...)
```

Use `not eq(...)` instead of `neq`.

### Constants

* Strings: `'text'`
* Numbers: `0`, `1`, `42`

---

## 10. Truthiness Rules

In conditions, bare sources mean:

```txt
exists AND parses successfully
```

Examples:

```txt
in
git
env:VERSION
spec
```

So:

```txt
[in]
```

means: input exists and is valid.

---

## 11. Format Checks

Require a specific version standard:

```txt
in:pep440
git:semver
env:VERSION:nuget
```

Meaning:

```txt
exists AND parses AND matches format
```

Supported formats:

* `pep440`
* `semver`
* `nuget`
* `calver`
* `loose`
* `unknown`

---

## 12. Condition Examples

Prefer env VERSION if valid PEP 440:

```txt
[env:VERSION:pep440] {env:VERSION}
```

Use input override:

```txt
[in] {in}
```

Only when commits exist:

```txt
[gt(git:distance, 0)] ...
```

Skip dirty builds:

```txt
[git and not git:dirty] ...
```

Reject unknown formats:

```txt
[not eq(in:standard, 'unknown')] ...
```

---

## 13. Complete Example

```toml
[tool.poetry-version-pattern]
patterns = [
  "[git:dirty] {git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}.dirty",
  "[in] {in}",
  "[env:BUILD_NUMBER] {git:major}.{git:minor}.{git:patch}.post{git:distance}+ci.{env:BUILD_NUMBER}+g{git:hash}",
  "[git] {git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}",
  "{spec}"
]
```

Behavior:

1. Dirty builds are marked
2. Explicit input wins
3. CI builds include build number
4. Git-based version is used
5. Fallback to spec

---

## 14. Parsing Rules

The plugin automatically detects:

* PEP 440
* SemVer
* NuGet
* CalVer
* Loose fallback

All parsed versions are normalized internally.

---

## 15. Error Handling

* Missing fields use defaults
* Failed parsing uses defaults or fallbacks
* No matching pattern produces an error

In verbose mode, resolution steps are logged.

---

## 16. Best Practices

For PyPI publishing, use PEP 440-compatible patterns:

```txt
{git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}
```

Avoid `-rc` in output.

For internal builds, metadata is acceptable:

```txt
{spec}+{git:hash}.{date:yyyyMMdd}
```

Always place dirty rules first.

---

## 17. Summary

A version is generated as:

```txt
Patterns -> Conditions -> First Match -> Tag Expansion -> Output
```

Key features:

* Multi-standard parsing
* Deterministic defaults
* Git-aware
* CI-friendly
* Minimal DSL
* Human-readable configuration

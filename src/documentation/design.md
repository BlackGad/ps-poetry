# Custom Version Pattern Specification

This plugin allows you to define how your package version is generated using declarative patterns.

A version is produced by evaluating a list of patterns. Each pattern may have an optional condition. The first matching pattern is used.

The system supports:

* SemVer, PEP 440, NuGet, CalVer, and hybrid versions
* Git-based versioning
* CI / environment variables
* Date- and random-based generation
* Safe defaults and fallbacks

## Default Behavior

If no `patterns` configuration is provided, the following default sequence is used:

```txt
{in} -> {env:BUILD_VERSION} -> {spec} -> 0.0.0
```

Meaning:

1. Use `--build-version` input if provided
2. Otherwise use `BUILD_VERSION` environment variable
3. Otherwise use version from `pyproject.toml`
4. Otherwise fall back to `0.0.0`

## Configuration

Define patterns in `pyproject.toml`:

```toml
[tool.poetry-version-pattern]
patterns = [
  "[{git:dirty}] {git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}.dirty",
  "[{in}] {in}",
  "[{env:BUILD_NUMBER}] {git:major}.{git:minor}.{git:patch}.post{git:distance}+ci.{env:BUILD_NUMBER}+g{git:hash}",
  "{spec}"
]
```

Patterns are evaluated top to bottom. The first matching entry wins.

## Pattern Format

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
['pep440' in {in:standards}] {in}
```

## Tags in Patterns

Patterns may contain tags:

```txt
{expression}
```

An expression has the form:

```txt
source[:name][:modifier...][<fallback>]
```

## Sources

| Source     | Description                            |
| ---------- | -------------------------------------- |
| `spec`     | Version from pyproject.toml            |
| `in`       | Version from --build-version argument  |
| `git`      | Selected Git tag                       |
| `env:NAME` | Environment variable                   |

Raw access:

If no modifier is given, the raw value is returned.

Examples:

```txt
{spec}
{in}
{git}
{env:VERSION}
```

## Accessors (Value Modifiers)

### Core numbers

| Modifier | Meaning            | Default |
| -------- | ------------------ | ------- |
| `major`  | First number       | 0       |
| `minor`  | Second number      | 0       |
| `patch`  | Third number       | 0       |
| `rev`    | Fourth number      | 0       |
| `core`   | All numbers joined | 0       |

### Pre-release

| Modifier     | Meaning          | Default |
| ------------ | ---------------- | ------- |
| `pre`        | Full pre-release | ""      |
| `pre:name`   | Label            | ""      |
| `pre:number` | Number           | 0       |

### PEP 440

| Modifier | Meaning     | Default |
| -------- | ----------- | ------- |
| `dev`    | Dev number  | 0       |
| `post`   | Post number | 0       |

### Metadata

| Modifier           | Meaning       | Default |
| ------------------ | ------------- | ------- |
| `metadata`         | Full metadata | ""      |
| `metadata:parts:0` | First part    | ""      |
| `metadata:parts:1` | Second part   | ""      |

### Git-only

| Modifier   | Meaning           | Default |
| ---------- | ----------------- | ------- |
| `hash`     | Commit hash       | ""      |
| `distance` | Commits since tag | 0       |
| `dirty`    | Dirty flag        | false   |

### Classification

| Modifier    | Meaning          |
| ----------- | ---------------- |
| `standards` | Detected formats |

## Generators

### Date

```txt
{date:<format>}
```

Formats the current date and time. When no format is provided, returns the date in `YYYY-MM-DD` form.

Three format styles are supported and may be mixed freely within a single format string:

**C#-style custom tokens**

| Token  | Meaning           | Example output |
| ------ | ----------------- | -------------- |
| `yyyy` | 4-digit year      | `2026`         |
| `yy`   | 2-digit year      | `26`           |
| `MM`   | 2-digit month     | `03`           |
| `dd`   | 2-digit day       | `12`           |
| `HH`   | 24-hour hour      | `14`           |
| `mm`   | 2-digit minute    | `05`           |
| `ss`   | 2-digit second    | `09`           |

**Python strftime directives**

Any `%X` directive (e.g. `%Y`, `%m`, `%H`) is passed through to `strftime` unchanged.

```txt
{date:%Y-%m-%d}
{date:%H%M%S}
```

Mixed C# and Python tokens in the same format are supported:

```txt
{date:yyyy-%m-dd}
```

**Standard named formats**

| Name        | Aliases   | Output example                      | Notes                                 |
| ----------- | --------- | ------------------------------------ | ------------------------------------- |
| `iso`       |           | `2026-03-12T16:05:09+00:00`          | ISO 8601, seconds precision           |
| `iso-round` | `o`, `O`  | `2026-03-12T16:05:09.123456+00:00`   | ISO 8601, microseconds precision      |
| `sortable`  | `s`       | `2026-03-12T16:05:09`                | Similar to .NET `s` specifier         |
| `universal` | `u`       | `2026-03-12 16:05:09Z`               | UTC; converts timezone-aware inputs   |

Examples:

```txt
{date:yyyy.MM.dd}
{date:yyMM}
{date:yyyyMMdd}
{date:iso}
{date:sortable}
{date:o}
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

## Fallback Values

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

## Conditions

Conditions control which pattern is selected. They appear inside `[ ]`.

### Operators

```txt
and
or
not
( )
```

### Constants

* Strings: `'text'`
* Numbers: `0`, `1`, `42`

## Truthiness Rules

In conditions, source tokens mean:

```txt
exists AND parses successfully
```

Examples:

```txt
{in}
{git}
{env:VERSION}
{spec}
```

So:

```txt
[{in}]
```

means: input exists and is valid.

## Format Checks

To require a specific version format, use the `in` operator with the `standards` accessor:

```txt
'<format>' in {<source>:standards}
```

Examples:

```txt
['pep440' in {in:standards}] {in}
['semver' in {git:standards}] {git}
['nuget' in {env:VERSION:standards}] {env:VERSION}
```

Supported format values:

* `pep440`
* `semver`
* `nuget`
* `calver`
* `loose`

## Condition Examples

Use input override:

```txt
[{in}] {in}
```

Require PEP 440 input:

```txt
['pep440' in {in:standards}] {in}
```

Skip dirty builds:

```txt
[{git} and not {git:dirty}] ...
```

## Complete Example

```toml
[tool.poetry-version-pattern]
patterns = [
  "[{git:dirty}] {git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}.dirty",
  "[{in}] {in}",
  "[{env:BUILD_NUMBER}] {git:major}.{git:minor}.{git:patch}.post{git:distance}+ci.{env:BUILD_NUMBER}+g{git:hash}",
  "[{git}] {git:major}.{git:minor}.{git:patch}.post{git:distance}+g{git:hash}",
  "{spec}"
]
```

Behavior:

1. Dirty builds are marked
2. Explicit input wins
3. CI builds include build number
4. Git-based version is used
5. Fallback to spec

## Parsing Rules

The plugin automatically detects:

* PEP 440
* SemVer
* NuGet
* CalVer
* Loose fallback

All parsed versions are normalized internally.

## Error Handling

* Missing fields use defaults
* Failed parsing uses defaults or fallbacks
* No matching pattern produces an error

In verbose mode, resolution steps are logged.

## Best Practices

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

## Summary

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

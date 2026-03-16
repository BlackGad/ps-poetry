# Overview

The `ps-plugin-module-delivery` module automates building and publishing packages across a monorepo. It extends Poetry's `build` and `publish` commands with unified version stamping, dependency constraint resolution, and topologically-ordered publish waves. A standalone `delivery` command displays the planned build and publish dependency tree without executing it.

The module is registered as a `ps.module` entry point and activates when included in the host project's `[tool.ps-plugin]` configuration.

# Installation

```bash
pip install ps-plugin-module-delivery
```

Or with Poetry:

```bash
poetry add ps-plugin-module-delivery
```

Enable it in the plugin configuration:

```toml
[tool.ps-plugin]
modules = ["ps-delivery"]
```

# Quick Start

Build all deliverable projects with a specific version:

```bash
poetry build -b 1.2.3
```

Publish all deliverable projects:

```bash
poetry publish -b 1.2.3
```

Preview the delivery plan without executing:

```bash
poetry delivery
```

# Configuration

The module reads its settings from the `[tool.ps-plugin]` section of the host project's `pyproject.toml`. Individual projects may also define their own `[tool.ps-plugin]` section to override the host-level defaults for that specific project.

```toml
[tool.ps-plugin]
version-patterns = [
    "[{in}] {in}",
    "[{env:BUILD_VERSION}] {env:BUILD_VERSION}",
    "{spec}"
]
version-pinning = "compatible"
```

* `version-patterns` — Ordered list of version expression patterns. Each pattern is evaluated in sequence; the first one whose condition matches and whose expression produces a valid version wins. See **Version Patterns** below.
* `version-pinning` — Constraint mode applied when resolving inter-project dependency versions. Accepts `compatible`, `exact`, `minimum-only`, `range-next-major`, `range-next-minor`, or `range-next-patch`. Defaults to `compatible`.
* `deliver` — Controls whether a project is included in the delivery scope. Set to `false` to exclude a project from all delivery operations. Defaults to `true` when not specified.

Individual projects can also opt out of delivery by setting `package-mode = false` in their `[tool.poetry]` section. When `package-mode = false`, the project is excluded regardless of the `deliver` setting.

# Command-Line Usage

## Build

```bash
poetry build [INPUTS...] [--build-version VERSION]
```

* `INPUTS` — Optional list of project names or paths. When omitted, all deliverable projects are built.
* `--build-version` / `-b` — Override the computed version for all projects.

The build stage patches all `pyproject.toml` files with resolved versions and dependency constraints, executes builds in parallel, then restores the original files.

## Publish

```bash
poetry publish [INPUTS...] [--build-version VERSION] [--repository REPO] [--dry-run] [--skip-existing]
```

* `INPUTS` — Optional list of project names or paths.
* `--build-version` / `-b` — Override the computed version.
* Standard Poetry publish options (`--repository`, `--username`, `--password`, `--cert`, `--client-cert`, `--dist-dir`, `--dry-run`, `--skip-existing`) are passed through.

The publish stage processes projects in topological order, respecting inter-project dependencies so that each package is available before its dependents are published.

## Delivery

```bash
poetry delivery
```

Displays the dependency tree and publish wave ordering for all deliverable projects. No files are modified.

# Version Patterns

Version patterns control how project versions are resolved during delivery. Each pattern follows the format:

```txt
[CONDITION] EXPRESSION
```

* The optional `[CONDITION]` is a boolean expression that must evaluate to true for the pattern to be selected.
* The `EXPRESSION` is a template string containing tokens in curly braces that is expanded to produce the version.

Patterns are evaluated in order. The first pattern whose condition is satisfied and whose expression produces a valid parseable version is used. If no pattern matches, the project's existing version remains unchanged.

## Pattern Syntax

A pattern expression may contain one or more tokens:

```txt
{source}
{source:accessor}
{source:accessor<fallback>}
```

Multiple tokens may be combined to compose a version string:

```txt
{git:version:major}.{git:version:minor}.{git:distance}
```

## Default Patterns

When `version-patterns` is not configured, the following defaults apply:

```toml
version-patterns = [
    "[{in}] {in}",
    "[{env:BUILD_VERSION}] {env:BUILD_VERSION}",
    "{spec}"
]
```

This means: use the `--build-version` input if provided, otherwise check the `BUILD_VERSION` environment variable, otherwise fall back to the version declared in `pyproject.toml`.

## Fallback Values

Each token may declare a fallback value inside angle brackets. Fallbacks are applied when the source is absent, fails to parse, or the requested field does not exist:

```txt
{in:minor<0>}
{env:VERSION<'1.0.0'>}
{git:version:distance<0>}
```

When no fallback is specified, the following type-based defaults are used:

| Type    | Default |
| ------- | ------- |
| Number  | `0`     |
| String  | `""`    |
| Boolean | `false` |

## Token Resolvers

Patterns use the token expression syntax from `ps-token-expressions` with several built-in resolvers:

* `{in}` — The input version passed via `--build-version`. Supports all version accessors.
* `{spec}` — The project's version from its `pyproject.toml`. Falls back to the host project version when the project version is `0.0.0`.
* `{env:VAR_NAME}` — Value of the environment variable `VAR_NAME`.
* `{git:ACCESSOR}` — Git repository metadata. See **Git Resolver** below.
* `{v:VERSION:ACCESSOR}` — Parse a literal or computed version string and extract a component. See **Parse Version Resolver** below.
* `{date:FORMAT}` — Current date and time formatted according to `FORMAT`. See **Date Formats** below.
* `{rand:KIND}` — Random values. See **Random Values** below.

### Version Accessors

The following accessors apply to any version-bearing source (`in`, `spec`, `git:version`, `v:...`):

| Accessor           | Meaning                                       |
| ------------------ | --------------------------------------------- |
| `major`            | First version number                          |
| `minor`            | Second version number                         |
| `patch`            | Third version number                          |
| `rev`              | Fourth version number                         |
| `core`             | All core numbers joined as a string           |
| `pre`              | Full pre-release label                        |
| `pre:name`         | Pre-release label name                        |
| `pre:number`       | Pre-release label number                      |
| `dev`              | PEP 440 dev segment number                    |
| `post`             | PEP 440 post segment number                   |
| `metadata`         | Full build metadata string                    |
| `metadata:parts:N` | Nth part of build metadata (zero-indexed)     |
| `standards`        | Set of detected format names (for conditions) |

Examples:

```txt
{in:major}.{in:minor}.{in:patch}
{spec:major}.{spec:pre:name}{spec:pre:number}
{spec:metadata:parts:0}
```

### Git Resolver

The `{git}` token provides access to Git repository state. Used without an accessor, it returns the version string parsed from the most recent annotated tag.

| Accessor   | Meaning                                         |
| ---------- | ----------------------------------------------- |
| `version`  | Parsed version from the most recent tag         |
| `sha`      | Short commit hash                               |
| `distance` | Commits since the last tag                      |
| `dirty`    | True when there are uncommitted changes         |
| `branch`   | Current branch name                             |
| `main`     | Default branch name resolved from `origin/HEAD` |
| `mainline` | True when the current branch is the main branch |

The `version` accessor supports all standard version accessors:

```txt
{git:version:major}.{git:version:minor}.{git:distance}
{git:version:pre:name}{git:version:pre:number}
```

### Parse Version Resolver

The `{v:VERSION:ACCESSOR}` token parses an arbitrary version string and extracts a single component. The `VERSION` argument may be a literal string or a nested token expression, making it possible to parse environment variables or other dynamic values and extract individual parts.

```txt
{v:3.5.1:major}               → 3
{v:{env:BUILD_VERSION}:minor} → minor component of BUILD_VERSION
{v:{in}:patch}                → patch component of the input version
```

### Date Formats

The `{date:FORMAT}` token resolves to the current date and time. When no format is given, it returns the current Unix timestamp as an integer.

**Standard named formats:**

| Name        | Aliases  | Example output                     |
| ----------- | -------- | ---------------------------------- |
| `unix`      |          | `1741791909` (integer timestamp)   |
| `ticks`     |          | `638780915090000000` (.NET ticks)  |
| `iso`       |          | `2026-03-12T16:05:09+00:00`        |
| `iso-round` | `o`, `O` | `2026-03-12T16:05:09.123456+00:00` |
| `sortable`  | `s`      | `2026-03-12T16:05:09`              |
| `universal` | `u`      | `2026-03-12 16:05:09Z`             |

**C#-style custom tokens:**

| Token  | Meaning         | Example |
| ------ | --------------- | ------- |
| `yyyy` | 4-digit year    | `2026`  |
| `yy`   | 2-digit year    | `26`    |
| `MM`   | 2-digit month   | `03`    |
| `dd`   | 2-digit day     | `12`    |
| `HH`   | 24-hour hour    | `14`    |
| `mm`   | 2-digit minute  | `05`    |
| `ss`   | 2-digit second  | `09`    |

Python `strftime` directives (e.g., `%Y`, `%m`, `%H`) are also accepted and may be mixed with C#-style tokens in the same format string.

Examples:

```txt
{date:yyyy.MM.dd}
{date:yyyyMMdd}
{date:yyyy-%m-dd}
{date:iso}
{date:sortable}
{date:o}
```

### Random Values

The `{rand}` resolver generates non-deterministic values. A kind argument is always required.

| Token                 | Description                           |
| --------------------- | ------------------------------------- |
| `{rand:uuid}`         | UUID v4 as 32-character hex string    |
| `{rand:hash}`         | 8-character lowercase hex string      |
| `{rand:num}`          | Random non-negative integer           |
| `{rand:num:MIN..MAX}` | Random integer in the inclusive range |

Examples:

```txt
{rand:uuid}
{rand:num:1..100}
```

### Custom Token Resolvers

Additional token resolvers can be registered through the DI container. Implement `IVersionTokenResolver` from `ps.plugin.module.delivery`, declare a `name: ClassVar[str]` for the token source, and implement `get_resolver()` to return the resolver callable:

```python
from typing import Any, ClassVar, Optional
from ps.plugin.module.delivery import IVersionTokenResolver
from ps.token_expressions import BaseResolver
from ps.token_expressions.token_resolvers._base_resolver import TokenValue


class MyResolver(BaseResolver):
    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        return args[0] if args else None


class MyTokenResolver(IVersionTokenResolver):
    name: ClassVar[str] = "my"

    def get_resolver(self) -> Any:
        return MyResolver()
```

Register the implementation through the DI container in a plugin module's `handle_activate` method:

```python
di.register(IVersionTokenResolver).implementation(MyTokenResolver)
```

Once registered, the token `{my:value}` becomes available in all version patterns.

## Condition Syntax

Conditions appear in the optional `[...]` block at the start of a pattern and evaluate to a boolean. A source token evaluates to true when the source exists and parses successfully. Conditions support boolean operators:

```txt
and   or   not   ( )
```

Condition examples:

```txt
[{in}]
[{git} and not {git:dirty}]
[{git:mainline} and {git:dirty}]
[{env:BUILD_NUMBER} or {env:CI}]
[not {git:dirty} and ({in} or {env:BUILD_VERSION})]
```

### Format Checks

To verify that a source version conforms to a specific standard, use the `in` operator with the `standards` accessor:

```txt
['pep440' in {in:standards}] {in}
['semver' in {git:version:standards}] {git:version}
['nuget' in {env:VERSION:standards}] {env:VERSION}
```

Supported format names: `pep440`, `semver`, `nuget`, `calver`, `loose`.

## Example: Git-Based Versioning

```toml
version-patterns = [
    "[{in}] {in}",
    "[{git:mainline} and {git:dirty}] {git:version:major}.{git:version:minor<0>}.{git:distance}+{date:%Y%m%d%H%M}",
    "[{git:mainline}] {git:version:major}.{git:version:minor<0>}.{git:distance}",
    "[{git:dirty}] {git:version:major}.{git:version:minor<0>}.{git:distance}+{git:branch}.{date:%Y%m%d%H%M}",
    "{git:version:major}.{git:version:minor<0>}.{git:distance}+{git:branch}"
]
```

This configuration resolves versions as follows:

* If `--build-version` is provided, use it directly.
* On the main branch with uncommitted changes, produce a version with a date-based build metadata suffix.
* On the main branch without uncommitted changes, produce a clean version from the git tag and distance.
* On a feature branch with uncommitted changes, include the branch name and date in build metadata.
* On a feature branch without uncommitted changes, include only the branch name in build metadata.

# Dependency Ordering

The delivery module resolves inter-project dependencies and organizes projects into publish waves. Each wave contains projects whose dependencies have all been published in previous waves.

```txt
Publish order:
  ├── Wave 1
  │   ├── ps-version
  │   └── ps-token-expressions
  └── Wave 2
      ├── ps-plugin-sdk
      └── ps-plugin-module-delivery
```

Projects within the same wave are processed in parallel during the build stage. During the publish stage, topological ordering ensures each project is published only after all of its dependencies are available.

# Project Backup and Restore

Before any delivery operation, the module backs up all `pyproject.toml` files in the environment. After the operation completes — whether successfully or with an error — the original files are restored. This prevents accidental corruption of source projects during version patching.

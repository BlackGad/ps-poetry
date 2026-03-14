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

The module reads its settings from the `[tool.ps-plugin]` section of the host project's `pyproject.toml`.

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

Individual projects can opt out of delivery by setting `package-mode = false` in their `[tool.poetry]` section.

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

* The optional `[CONDITION]` is a token expression that must evaluate to a truthy value for the pattern to be considered.
* The `EXPRESSION` is evaluated to produce the version string.

Patterns are evaluated in order. The first pattern whose condition is satisfied and whose expression produces a valid parseable version is used. If no pattern matches, the project's existing version remains unchanged.

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

## Token Resolvers

Patterns use the token expression syntax from `ps-token-expressions` with several built-in resolvers:

* `{in}` — The input version passed via `--build-version`. Supports accessors: `{in:major}`, `{in:minor}`, `{in:patch}`.
* `{spec}` — The project's version from its `pyproject.toml`.
* `{env:VAR_NAME}` — Value of the environment variable `VAR_NAME`.
* `{git:ACCESSOR}` — Git repository metadata. Accessors include `version` (parsed from the latest tag), `sha` (short commit hash), `distance` (commits since last tag), `dirty` (uncommitted changes), `branch` (current branch), and `mainline` (whether the current branch is the main branch). The `version` accessor supports nested accessors like `{git:version:major}`.
* `{v:VERSION:ACCESSOR}` — Parse a version string and extract components. Example: `{v:3.5.1:major}` produces `3`.
* `{date:FORMAT}` — Current date/time. Supports `unix`, `ticks`, `sortable`, `iso`, and custom .NET-style format strings like `yyyy-MM-dd`.
* `{rand:KIND}` — Random values. Kinds: `uuid`, `hash` (8-char hex), `num` (integer, optionally with `MIN..MAX` range).

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

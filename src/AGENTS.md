
# AI Agent Instructions for ps-poetry

This document defines the core rules that apply to all operations within the ps-poetry repository.

## Specialized Skills

The following skills provide detailed instructions for specific subtasks and are invoked automatically when relevant:

* **documentation** — creating or updating README files, example files, and documentation structure
* **linting** — running ruff, fixing lint errors, Pylance issues, and markdown linting
* **testing** — creating or modifying unit test files in `tests/` directories

## Workspace Structure Reference

The workspace is a monorepo containing the ps-poetry Poetry plugin and its components:

* **`./`** — Workspace root folder
* **`plugin/`** — Core Poetry plugin (`ps-plugin-core`); entry point registered as `poetry.application.plugin`
* **`plugin/src/ps/plugin/core/`** — Plugin core source code
* **`plugin/tests/`** — Plugin unit tests
* **`sdk/`** — Plugin SDK package (`ps-plugin-sdk`); shared interfaces, models, protocols, helpers
* **`sdk/src/ps/plugin/sdk/`** — SDK source code
* **`sdk/tests/`** — SDK unit tests
* **`modules/check/`** — Check module (`ps-plugin-module-check`)
* **`modules/delivery/`** — Delivery module (`ps-plugin-module-delivery`)
* **`modules/monorepo/`** — Monorepo module (`ps-plugin-module-monorepo`)
* **`modules/<name>/src/`** — Module source code
* **`modules/<name>/tests/`** — Module unit tests
* **`libraries/version/`** — Version parsing library (`ps-version`)
* **`libraries/token_expressions/`** — Token expression library (`ps-token-expressions`)
* **`libraries/di/`** — Dependency injection library (`ps-di`)
* **`libraries/<name>/src/`** — Library source code
* **`libraries/<name>/tests/`** — Library unit tests
* **`experiments/`** — Experimental usage scripts (do not modify)

## Running Tools

All commands must be executed from the workspace root (`src/`) using Poetry.

### Linting

Run Ruff linter on the entire codebase:

```bash
poetry run --no-plugins ruff check .
```

Run Ruff linter on a specific file or directory:

```bash
poetry run --no-plugins ruff check <path>
```

### Testing

Run all tests:

```bash
poetry run --no-plugins pytest
```

Run tests for a specific file:

```bash
poetry run --no-plugins pytest <path/to/test_file.py>
```

Run a specific test:

```bash
poetry run --no-plugins pytest <path/to/test_file.py>::<test_name>
```

Run tests with verbose output:

```bash
poetry run --no-plugins pytest -v
```

## Code Usage Analysis

### Reference Sources

* Scan source code in `plugin/src/`, `sdk/src/`, `modules/*/src/`, `libraries/*/src/`
* Review experiment files in `experiments/` for real-world usage patterns
* Cross-verify consistency between source code, experiments, and documentation

### Integration Rules

* When creating documentation or examples, include usage patterns found in experiments if they demonstrate core plugin or library features
* Avoid duplicating code that already exists elsewhere in the codebase
* Never modify files in the `experiments/` directory

## Code Style Rules

### Imports

* Order: `stdlib → third-party → local`, separated by blank lines between groups
* Do NOT use `from __future__ import annotations`
* Do NOT use `TYPE_CHECKING` guards
* When importing more than 3 names from a single module, use parenthesized multi-line syntax:

  ```python
  from some.module import (
      NameOne,
      NameTwo,
      NameThree,
      NameFour,
  )
  ```

### Type Hints

* Nullable types: `Optional[X]` — never `X | None`
* `|` union operator is acceptable in function signatures (e.g., `str | SpecifierSet`)
* Type hints are mandatory on all function parameters and return values

### Naming

* Functions and variables: `snake_case`
* Classes: `PascalCase`
* Private methods, attributes, and module files: `_single_underscore_prefix`
* Constants (`ClassVar`) and all enum members: `UPPER_SNAKE_CASE`

### Strings

* Double quotes everywhere; single quotes only when the string itself contains a double quote

### Classes

* Abstract interfaces: inherit from both `Protocol` and `ABC`; always apply `@runtime_checkable`
* Method order within a class: `__init__` → special methods → `@property`/`@computed_field` → public methods → private methods

### File / Module Structure

* Private implementation in `_*.py` files
* Public API exposed through `__init__.py` with explicit `__all__`
* Imports re-exported in `__init__.py`: `from ._module import Symbol`

## Code Generation Rules

* **Docstrings Policy** — **DO NOT generate docstrings unless the user explicitly requests them.** When explicitly requested:
  * Add docstrings ONLY to public classes and methods (not prefixed with `_`)
  * Location: ONLY in main codebase under `plugin/src/`, `sdk/src/`, `modules/*/src/`, or `libraries/*/src/`
  * Format: Brief one-line or multi-line description without parameter documentation (`Args:`, `Returns:`, etc.) and without usage examples
  * NEVER add docstrings to files in `tests/` or `experiments/` directories
* Analyze code structure in the target directory before generating code to identify existing patterns (naming conventions, type hints usage, error handling approaches)
* Match indentation style (spaces vs tabs), import organization, and code structure of adjacent files in the same directory

## General Principles

* **Accuracy First**
* **Minimal Changes**
* **Consistency**
* **Environment Respect**
* **Lint-Clean State** — ALWAYS validated using the linting skill
* **Test Integrity** — ALWAYS validated using the testing skill
* **Docstring Policy** — **DO NOT generate docstrings unless explicitly requested by user.** When explicitly requested: docstrings allowed ONLY in main codebase under `plugin/src/`, `sdk/src/`, `modules/*/src/`, and `libraries/*/src/`; PROHIBITED in `tests/` and `experiments/`; must be brief descriptions without parameter documentation sections (`Args:`, `Returns:`, etc.) or usage examples; apply ONLY to public classes and methods (not prefixed with `_`)

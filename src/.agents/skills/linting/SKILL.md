---
name: linting
description: 'Run linters, fix lint errors, static analysis, ruff checks, Pylance issues, markdown linting. Use when fixing ruff errors, resolving Pylance warnings, checking code style, or validating files before completion.'
---

# Static Analysis and Linting

## Linting Tool Selection

**Use the correct tool for the file type:**

* **For Python files (.py)** → Use **Pylance** and **ruff** as described below
* **For Markdown files (.md)** → Check **VS Code Problems panel** for markdown linting issues; do NOT use ruff or Python linters

## Python Linting Workflow

After modifying any Python file:

* Resolve all **Pylance** issues
* Resolve all **ruff** issues:
  * If ruff reports auto-fixable errors, run `poetry run ruff check --fix <path>` to automatically fix them
  * After auto-fix, verify the changes are correct and tests still pass
  * For errors that cannot be auto-fixed, manually correct the code according to ruff's recommendations

## Allowed Ruff Suppressions

Suppressing ruff warnings is only permitted in:

* **unit test files**
* **experiment files**

You may suppress only the following warnings in those contexts:

* `E501` — line too long
* `C901` — function is too complex
* `PLR0913` — too many arguments in function definition
* `PLR0915` — too many statements
* `PLR0912` — too many branches
* `PLR2004` — magic value used in comparison
* `S101` — use of assert detected

These apply **only** to test files and experiment files.

## Forbidden Suppressions in Core Codebase

In all **regular source files** (`plugin/src/`, `sdk/src/`, `modules/*/src/`, `libraries/*/src/`, excluding experiments):

* **Suppressing ruff errors or warnings is strictly prohibited.**
* You must fix the code **according to ruff's recommendation**, not silence the warning.

No exceptions.

## Ruff Execution Rules

* ALWAYS run ruff from the **workspace root directory** (`src/`)
* ALWAYS use the workspace `ruff.toml` configuration
* Make only the specific code changes required to resolve each reported error
* Do not restructure or refactor code beyond what is necessary to fix the linting issue
* Preserve existing code logic, variable names, and structure unless they directly cause the linting error

## Running Ruff Linter

All ruff commands must be executed from the workspace root (`src/`) using Poetry.

### Check Entire Codebase

```bash
poetry run ruff check .
```

### Check Specific File or Directory

```bash
poetry run ruff check <path>
```

### Check with Auto-fix

```bash
poetry run ruff check --fix <path>
```

**When to use auto-fix:**

* Ruff reports errors marked as fixable (safe automatic corrections)
* After auto-fix, ALWAYS verify the changes and run tests to ensure correctness

## Post-lint Verification

* After fixing lint errors in test files, verify that the test logic has not changed (same assertions, same test coverage)
* Run all modified tests to confirm they pass
* If tests fail after linting fixes, the linting change was too aggressive — revert and apply a more conservative fix

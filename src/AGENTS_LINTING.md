# Static Analysis and Linting Instructions

When performing linting or static analysis, follow this document alongside **AGENTS.md**.
When linting affects tests, consult **AGENTS_TESTS.md**.
When linting affects documentation code samples, refer to **AGENTS_DOCS.md**.

## Linting Workflow

After modifying any Python file:

1. Resolve all **Pylance** issues
2. Resolve all **ruff** issues

## Forbidden Suppressions in Core Codebase

In all **plugin source files** (anything under `plugin/src/ps/plugin/core/`):

* **Suppressing ruff errors or warnings is strictly prohibited.**
* You must fix the code **according to ruff's recommendation**, not silence the warning.

No exceptions.

## Ruff Execution Rules

* ALWAYS run ruff from the **workspace root directory**
* ALWAYS use the workspace `ruff.toml` configuration
* Use the command:

  ```bash
  poetry run ruff check <dir_with_py_files>
  ```

* Apply **minimal, targeted edits** to achieve a compliant state

## Post-lint Verification

* Ensure tests remain logically correct
* Tests must pass when executed via MCP

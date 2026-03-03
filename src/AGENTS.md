
# AI Agent Instructions for PS Poetry Plugin Project

This document establishes foundational rules for all operations within the PS Poetry Plugin project.

When your task involves **documentation**, refer to **AGENTS_DOCS.md**.
When your task involves **unit tests**, refer to **AGENTS_TESTS.md**.
When your task involves **linting or static analysis**, refer to **AGENTS_LINTING.md**.

## Project Structure

The workspace is organized as follows:

* **`plugin/`** — Core plugin implementation (ps-plugin-core)
  * **`src/ps/plugin/core/`** — Plugin source code
  * **`tests/`** — Plugin-specific tests
  * **`pyproject.toml`** — Plugin package configuration
* **`modules/`** — Extension modules for the plugin (future use)
* **`documentation/`** — Project documentation files
* **`experiments/`** — Experimental code and prototypes
* **`tests/`** — Workspace-level tests
* **`pyproject.toml`** — Workspace configuration
* **`launcher.py`** — Debug launcher for plugin development

### Plugin Core Structure

The core plugin (`plugin/src/ps/plugin/core/`) contains:

* **`plugin.py`** — Main plugin implementation
* **`__init__.py`** — Package initialization

## Code Analysis Guidelines

### Reference Sources

* Examine plugin source code in `plugin/src/ps/plugin/core/`
* Review test files for usage examples
* Verify consistency across the codebase

### Integration Principles

* Incorporate missing patterns when appropriate
* Prevent code duplication
* Preserve plugin architecture consistency

## Code Development Standards

* **Docstrings only when requested** — Generate docstrings only when the user explicitly asks for them
* **Relative imports within packages** — Always use relative imports (`.` prefix) for modules inside the same package; never use absolute imports for intra-package references
* **`__init__.py` policy** — Only the root `__init__.py` of a package should contain exports; all other (nested) `__init__.py` files must remain empty
* **`__all__` policy** — Never re-export in `__all__` types, classes, or symbols that originate from a different package; only export symbols defined within the current package
* **Module-scope imports** — Always import symbols from the package root (e.g., `from ps.plugin.sdk import Project`), never from individual module files (e.g., `from ps.plugin.sdk.models.project import Project`)
* **Grouped imports** — When importing multiple symbols from the same package, use the multi-line parenthesised form:

  ```python
  from package import (
      SymbolA,
      SymbolB,
  )
  ```
  
* Adhere to established code patterns and conventions
* Ensure consistency with existing code

## Core Principles

1. **Accuracy First**
2. **Minimal Changes**
3. **Consistency**
4. **Environment Respect**
5. **Lint-Clean State** — Always validated per AGENTS_LINTING.md
6. **Test Integrity** — Always validated per AGENTS_TESTS.md
7. **Docstring Policy** — Add docstrings only when explicitly requested by the user

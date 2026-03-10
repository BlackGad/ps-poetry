---
name: testing
description: 'Create, update, review, or fix unit test files in tests/ directories. Use when writing new tests, modifying existing tests, adding pytest fixtures, or validating test coverage for a component.'
---

# Unit Testing Guidelines

## Project and File Management

* Identify the component/package by locating its `pyproject.toml` file or by examining the folder context
* Maintain the directory structure mapping: plugin source at `plugin/src/.../x.py` maps to `plugin/tests/test_x.py`; SDK source at `sdk/src/.../x.py` maps to `sdk/tests/test_x.py`; module source at `modules/<name>/src/.../x.py` maps to `modules/<name>/tests/test_x.py`; library source at `libraries/<name>/src/.../x.py` maps to `libraries/<name>/tests/test_x.py`
* Do not create test files for `__init__.py` files
* Only create or modify files within each component's `tests/` directory; do not modify source code files

## Code Standards

* Place all imports at the top of the test file, following standard Python conventions
* Before writing test code, read the actual source files to verify correct import paths and available classes/methods
* Use `@pytest.fixture` for test setup and `unittest.mock.MagicMock` for mocking dependencies
* **NO docstrings in test files** — test files must not contain docstrings

## Test Execution Environment

* Run tests from the **workspace root** using Poetry commands
* Do not modify environment paths
* Assume Python environment is already configured

## Running Tests

All test commands must be executed from the workspace root (`src/`) using Poetry.

### Run All Tests

```bash
poetry run pytest
```

### Run Tests for a Specific File

```bash
poetry run pytest <path/to/test_file.py>
```

### Run a Specific Test

```bash
poetry run pytest <path/to/test_file.py>::<test_name>
```

### Run Tests with Verbose Output

```bash
poetry run pytest -v
```

### Run Tests with Coverage

```bash
poetry run pytest --cov
```

## Test Development Strategy

* When adding new tests, ensure they cover the functionality described in the user's request
* When updating existing tests, preserve passing tests that correctly validate the intended behavior
* Only rewrite tests if they are failing due to outdated assumptions or incorrect assertions
* After making changes to imports or code structure, re-read the source files to verify all references are still valid


# Unit Testing Guidelines

When creating or modifying unit tests, follow this document alongside **AGENTS.md**.
When test changes affect documentation, refer to **AGENTS_DOCS.md**.
When test files require lint cleanup, refer to **AGENTS_LINTING.md**.

## Project and File Management

* Identify project context via folder structure or `pyproject.toml` files
* Maintain directory mapping (`plugin/src/ps/plugin/core/x.py` → `plugin/tests/test_x.py`)
* Skip testing `__init__.py` files
* Modify only test files

## Code Standards

* Place imports at top
* Validate imports by scanning actual source files
* Use `@pytest.fixture` and `MagicMock`

## Test Execution Environment

* Run tests ONLY using the `test tool`
* Do not modify environment paths
* Assume Python environment is already configured

## Test Development Strategy

* Add/update tests to match current code
* Do not rewrite correct tests
* Re-scan imports after changes

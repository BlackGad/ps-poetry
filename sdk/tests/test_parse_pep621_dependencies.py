from tomlkit import parse
from packaging.specifiers import SpecifierSet

from ps.plugin.sdk.project import (
    parse_dependencies_from_document,
    parse_project,
)


def test_parse_pep621_simple_dependencies():
    content = """
[project]
dependencies = [
    "requests>=2.31.0",
    "fastapi>=0.110,<1.0",
    "pydantic==2.6.1",
]
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 3

    assert deps[0].name == "requests"
    assert deps[0].version == ">=2.31.0"

    assert deps[1].name == "fastapi"
    # SpecifierSet normalizes the order
    assert deps[1].version in (">=0.110,<1.0", "<1.0,>=0.110")

    assert deps[2].name == "pydantic"
    assert deps[2].version == "==2.6.1"


def test_parse_pep621_dependencies_with_extras():
    content = """
[project]
dependencies = [
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio,mypy]~=2.0",
]
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 2

    assert deps[0].name == "uvicorn"
    assert deps[0].version == ">=0.27.0"
    assert deps[0].extras == ["standard"]

    assert deps[1].name == "sqlalchemy"
    assert deps[1].version == "~=2.0"
    assert deps[1].extras is not None
    assert set(deps[1].extras) == {"asyncio", "mypy"}


def test_parse_pep621_dependencies_with_markers():
    content = """
[project]
dependencies = [
    "rich; python_version >= '3.10'",
    "pywin32; sys_platform == 'win32'",
]
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 2

    assert deps[0].name == "rich"
    # Marker normalization uses double quotes
    assert deps[0].markers is not None
    assert "python_version" in deps[0].markers
    assert "3.10" in deps[0].markers

    assert deps[1].name == "pywin32"
    assert deps[1].markers is not None
    assert "sys_platform" in deps[1].markers
    assert "win32" in deps[1].markers


def test_parse_pep621_dependencies_complex():
    content = """
[project]
dependencies = [
    "requests[security,socks]>=2.25.0,!=2.26.0",
    "typing-extensions>=4.0; python_version < '3.11'",
]
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 2

    assert deps[0].name == "requests"
    # SpecifierSet normalizes the order
    assert deps[0].version in (">=2.25.0,!=2.26.0", "!=2.26.0,>=2.25.0")
    assert deps[0].extras is not None
    assert set(deps[0].extras) == {"security", "socks"}

    assert deps[1].name == "typing-extensions"
    assert deps[1].version == ">=4.0"
    # Marker normalization uses double quotes
    assert deps[1].markers is not None
    assert "python_version" in deps[1].markers
    assert "3.11" in deps[1].markers


def test_version_constraint_property():
    content = """
[project]
dependencies = [
    "requests>=2.31.0,<3.0",
    "fastapi",
]
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 2

    # First dependency has version constraint
    constraint = deps[0].version_constraint
    assert constraint is not None
    assert isinstance(constraint, SpecifierSet)
    assert "2.31.0" in constraint
    assert "3.0.0" not in constraint

    # Second dependency has no version constraint
    assert deps[1].version_constraint is None or len(deps[1].version_constraint) == 0


def test_update_version_pep621():
    content = """
[project]
name = "test-project"
dependencies = [
    "requests>=2.31.0",
    "fastapi[all]>=0.110; python_version >= '3.10'",
]
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    # Update first dependency
    deps[0].update_version(">=3.0.0")
    assert deps[0].version == ">=3.0.0"
    assert document["project"]["dependencies"][0] == "requests>=3.0.0"  # type: ignore[index]

    # Update second dependency (preserves extras and markers)
    deps[1].update_version(">=0.120.0")
    assert deps[1].version == ">=0.120.0"
    # Marker normalization uses double quotes
    updated_dep = document["project"]["dependencies"][1]  # type: ignore[index]
    assert "fastapi[all]>=0.120.0" in updated_dep  # type: ignore[operator]
    assert "python_version" in updated_dep  # type: ignore[operator]
    assert "3.10" in updated_dep  # type: ignore[operator]


def test_update_version_poetry_string():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.31.0"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1  # python is skipped

    deps[0].update_version("^3.0.0")
    assert deps[0].version == "^3.0.0"
    assert document["tool"]["poetry"]["dependencies"]["requests"] == "^3.0.0"  # type: ignore[index]


def test_update_version_poetry_dict():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mypackage = { version = "^1.0", extras = ["all"] }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1

    deps[0].update_version("^2.0")
    assert deps[0].version == "^2.0"
    assert document["tool"]["poetry"]["dependencies"]["mypackage"]["version"] == "^2.0"  # type: ignore[index]


def test_project_with_pep621_dependencies(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    content = """
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.31.0",
    "fastapi[all]>=0.110",
]
"""
    pyproject.write_text(content, encoding='utf-8')

    project = parse_project(pyproject)
    assert project is not None
    assert len(project.dependencies) == 2

    assert project.dependencies[0].name == "requests"
    assert project.dependencies[0].version == ">=2.31.0"

    assert project.dependencies[1].name == "fastapi"
    assert project.dependencies[1].version == ">=0.110"
    assert project.dependencies[1].extras == ["all"]


def test_mixed_pep621_and_poetry_dependencies():
    """Test that both PEP 621 and Poetry dependencies can coexist."""
    content = """
[project]
dependencies = [
    "requests>=2.31.0",
]

[tool.poetry.dependencies]
python = "^3.10"
numpy = "^1.24"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    # Should have both PEP 621 and Poetry dependencies
    assert len(deps) == 2

    pep621_dep = next((d for d in deps if d.name == "requests"), None)
    assert pep621_dep is not None
    assert pep621_dep.version == ">=2.31.0"

    poetry_dep = next((d for d in deps if d.name == "numpy"), None)
    assert poetry_dep is not None
    assert poetry_dep.version == "^1.24"

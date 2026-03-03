import pytest
from tomlkit import parse

from ps.plugin.sdk import TomlValue


def test_locate_existing_simple_value():
    content = """
[project]
name = "my-package"
version = "1.0.0"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert name.exists
    assert name.value == "my-package"
    assert name.jsonpath == "$.project.name"


def test_locate_existing_nested_value():
    content = """
[tool.poetry]
name = "poetry-package"
version = "2.0.0"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["tool.poetry.name"])

    assert name.exists
    assert name.value == "poetry-package"
    assert name.jsonpath == "$.tool.poetry.name"


def test_locate_with_multiple_candidates_picks_first_existing():
    content = """
[project]
name = "pep621-name"

[tool.poetry]
name = "poetry-name"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name", "tool.poetry.name"])

    assert name.exists
    assert name.value == "pep621-name"
    assert name.jsonpath == "$.project.name"


def test_locate_with_multiple_candidates_picks_second_when_first_missing():
    content = """
[tool.poetry]
name = "poetry-name"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name", "tool.poetry.name"])

    assert name.exists
    assert name.value == "poetry-name"
    assert name.jsonpath == "$.tool.poetry.name"


def test_locate_nonexistent_value_uses_fallback():
    content = """
[project]
description = "A test project"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert not name.exists
    assert name.value is None
    assert name.jsonpath == "$.project.name"


def test_locate_nonexistent_nested_value_uses_fallback():
    content = """
[tool]
other = "value"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["tool.poetry.name"])

    assert not name.exists
    assert name.value is None
    assert name.jsonpath == "$.tool.poetry.name"


def test_locate_empty_document_uses_fallback():
    content = ""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert not name.exists
    assert name.value is None
    assert name.jsonpath == "$.project.name"


def test_set_existing_value():
    content = """
[project]
name = "old-name"
version = "1.0.0"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert name.value == "old-name"

    name.set("new-name")

    assert name.value == "new-name"
    assert document["project"]["name"] == "new-name"  # type: ignore[index]


def test_set_value_in_nested_structure():
    content = """
[tool.poetry]
name = "old-package"
version = "1.0.0"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["tool.poetry.name"])

    assert name.value == "old-package"

    name.set("new-package")

    assert name.value == "new-package"
    assert document["tool"]["poetry"]["name"] == "new-package"  # type: ignore[index]


def test_set_value_with_different_types():
    content = """
[project]
name = "package"
"""
    document = parse(content)

    # Set string
    name = TomlValue.locate(document, ["project.name"])
    name.set("updated-name")
    assert name.value == "updated-name"

    # Set number
    document_with_version = parse("""
[project]
version = "1.0.0"
""")
    version = TomlValue.locate(document_with_version, ["project.version"])
    version.set("2.0.0")
    assert version.value == "2.0.0"


def test_exists_returns_false_for_missing_path():
    content = """
[project]
description = "test"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert not name.exists


def test_exists_returns_true_for_existing_path():
    content = """
[project]
name = "test-package"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert name.exists


def test_value_returns_none_for_missing_path():
    content = """
[project]
description = "test"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    assert name.value is None


def test_value_returns_correct_type():
    content = """
[project]
name = "test"
version = "1.0.0"

[tool.settings]
enabled = true
count = 42
"""
    document = parse(content)

    name = TomlValue.locate(document, ["project.name"])
    assert name.value == "test"
    assert isinstance(name.value, str)

    version = TomlValue.locate(document, ["project.version"])
    assert version.value == "1.0.0"
    assert isinstance(version.value, str)

    enabled = TomlValue.locate(document, ["tool.settings.enabled"])
    assert enabled.value is True
    assert isinstance(enabled.value, bool)

    count = TomlValue.locate(document, ["tool.settings.count"])
    assert count.value == 42
    assert isinstance(count.value, int)


def test_locate_with_empty_candidates_list():
    content = """
[project]
name = "test"
"""
    document = parse(content)
    result = TomlValue.locate(document, [])

    assert not result.exists
    assert result.value is None
    assert result.jsonpath is None


def test_set_raises_error_when_path_not_found():
    content = """
[project]
name = "test"
"""
    document = parse(content)
    result = TomlValue.locate(document, [])

    with pytest.raises(ValueError, match="Path not found"):
        result.set("value")


def test_model_dump_excludes_document():
    content = """
[project]
name = "test"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    dumped = name.model_dump()

    assert "document" not in dumped
    assert "jsonpath" in dumped
    assert "value" in dumped
    assert dumped["jsonpath"] == "$.project.name"
    assert dumped["value"] == "test"


def test_model_dump_includes_none_value():
    content = """
[project]
description = "test"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    dumped = name.model_dump()

    assert "value" in dumped
    assert dumped["value"] is None


def test_locate_deeply_nested_value():
    content = """
[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
"""
    document = parse(content)
    pytest_dep = TomlValue.locate(document, ["tool.poetry.group.dev.dependencies.pytest"])

    assert pytest_dep.exists
    assert pytest_dep.value == "^7.0.0"


def test_set_deeply_nested_value():
    content = """
[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
"""
    document = parse(content)
    pytest_dep = TomlValue.locate(document, ["tool.poetry.group.dev.dependencies.pytest"])

    pytest_dep.set("^8.0.0")

    assert pytest_dep.value == "^8.0.0"
    assert document["tool"]["poetry"]["group"]["dev"]["dependencies"]["pytest"] == "^8.0.0"  # type: ignore[index]


def test_locate_handles_special_characters_in_keys():
    content = """
[project]
"special-key-name" = "value"
"""
    document = parse(content)
    special = TomlValue.locate(document, ["project.special-key-name"])

    assert special.exists
    assert special.value == "value"


def test_multiple_set_operations():
    content = """
[project]
name = "initial"
version = "0.1.0"
"""
    document = parse(content)
    name = TomlValue.locate(document, ["project.name"])

    name.set("first-update")
    assert name.value == "first-update"

    name.set("second-update")
    assert name.value == "second-update"

    name.set("third-update")
    assert name.value == "third-update"

    assert document["project"]["name"] == "third-update"  # type: ignore[index]

from tomlkit import parse

from ps.plugin.sdk.helpers.parse_toml import parse_plugin_settings_from_document


def test_default_settings_when_section_missing():
    content = """
[tool.poetry]
name = "my-package"
version = "1.0.0"
"""
    document = parse(content)
    settings = parse_plugin_settings_from_document(document)

    assert settings.enabled is False


def test_enabled_true():
    content = """
[tool.ps-plugin]
enabled = true
"""
    document = parse(content)
    settings = parse_plugin_settings_from_document(document)

    assert settings.enabled is True


def test_enabled_false():
    content = """
[tool.ps-plugin]
enabled = false
"""
    document = parse(content)
    settings = parse_plugin_settings_from_document(document)

    assert settings.enabled is False


def test_extra_fields_allowed():
    content = """
[tool.ps-plugin]
enabled = true
custom_field = "value"
another_field = 42
"""
    document = parse(content)
    settings = parse_plugin_settings_from_document(document)

    assert settings.enabled is True
    assert settings.model_extra is not None
    assert settings.model_extra["custom_field"] == "value"
    assert settings.model_extra["another_field"] == 42


def test_empty_section():
    content = """
[tool.ps-plugin]
"""
    document = parse(content)
    settings = parse_plugin_settings_from_document(document)

    assert settings.enabled is True


def test_with_other_tool_sections():
    content = """
[tool.poetry]
name = "my-package"

[tool.ps-plugin]
enabled = true

[tool.ruff]
line-length = 120
"""
    document = parse(content)
    settings = parse_plugin_settings_from_document(document)

    assert settings.enabled is True

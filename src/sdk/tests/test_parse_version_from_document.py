from tomlkit import parse

from ps.plugin.sdk.helpers.parse_toml import parse_version_from_document


def test_get_version_from_pep621_format():
    content = """
[project]
version = "1.2.3"
"""
    document = parse(content)
    assert parse_version_from_document(document) == "1.2.3"


def test_get_version_from_poetry_format():
    content = """
[tool.poetry]
version = "3.4.5"
"""
    document = parse(content)
    assert parse_version_from_document(document) == "3.4.5"


def test_get_version_prefers_pep621_over_poetry():
    content = """
[project]
name = "my-package"
version = "1.0.0"

[tool.poetry]
name = "poetry-package"
version = "2.0.0"
"""
    document = parse(content)
    assert parse_version_from_document(document) == "1.0.0"


def test_get_version_returns_default_when_missing():
    content = """
[project]
"""
    document = parse(content)
    assert parse_version_from_document(document) is None


def test_get_version_from_empty_document():
    content = ""
    document = parse(content)
    assert parse_version_from_document(document) is None

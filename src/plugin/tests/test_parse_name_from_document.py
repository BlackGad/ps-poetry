from tomlkit import parse

from ps.plugin.core.parse_toml import parse_name_from_document


def test_get_name_from_pep621_format():
    content = """
[project]
name = "my-package"
"""
    document = parse(content)
    assert parse_name_from_document(document) == "my-package"


def test_get_name_from_poetry_format():
    content = """
[tool.poetry]
name = "poetry-package"
"""
    document = parse(content)
    assert parse_name_from_document(document) == "poetry-package"


def test_get_name_prefers_pep621_over_poetry():
    content = """
[project]
name = "pep621-name"

[tool.poetry]
name = "poetry-name"
"""
    document = parse(content)
    assert parse_name_from_document(document) == "pep621-name"


def test_get_name_returns_default_when_missing():
    content = """
[project]
"""
    document = parse(content)
    assert parse_name_from_document(document) is None


def test_get_name_from_empty_document():
    content = ""
    document = parse(content)
    assert parse_name_from_document(document) is None

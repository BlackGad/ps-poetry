from tomlkit import parse

from ps.plugin.sdk import (
    SourcePriority,
    parse_sources_from_document,
)


def test_no_sources_section():
    content = """
[tool.poetry]
name = "my-package"
version = "1.0.0"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert sources == []


def test_empty_sources_list():
    content = """
[tool.poetry]
name = "my-package"

[[tool.poetry.source]]
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    # Entry without "name" key is skipped
    assert sources == []


def test_single_source_name_only():
    content = """
[[tool.poetry.source]]
name = "pypi"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 1
    assert sources[0].name == "pypi"
    assert sources[0].url is None
    assert sources[0].priority is None


def test_single_source_full():
    content = """
[[tool.poetry.source]]
name = "my-index"
url = "https://example.com/simple/"
priority = "primary"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 1
    assert sources[0].name == "my-index"
    assert sources[0].url == "https://example.com/simple/"
    assert sources[0].priority == SourcePriority.PRIMARY


def test_multiple_sources():
    content = """
[[tool.poetry.source]]
name = "primary-index"
url = "https://primary.example.com/simple/"
priority = "primary"

[[tool.poetry.source]]
name = "secondary-index"
url = "https://secondary.example.com/simple/"
priority = "secondary"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 2
    assert sources[0].name == "primary-index"
    assert sources[0].priority == SourcePriority.PRIMARY
    assert sources[1].name == "secondary-index"
    assert sources[1].priority == SourcePriority.SECONDARY


def test_all_priority_values():
    content = """
[[tool.poetry.source]]
name = "s1"
priority = "default"

[[tool.poetry.source]]
name = "s2"
priority = "primary"

[[tool.poetry.source]]
name = "s3"
priority = "secondary"

[[tool.poetry.source]]
name = "s4"
priority = "supplemental"

[[tool.poetry.source]]
name = "s5"
priority = "explicit"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 5
    assert sources[0].priority == SourcePriority.DEFAULT
    assert sources[1].priority == SourcePriority.PRIMARY
    assert sources[2].priority == SourcePriority.SECONDARY
    assert sources[3].priority == SourcePriority.SUPPLEMENTAL
    assert sources[4].priority == SourcePriority.EXPLICIT


def test_unknown_priority_is_none():
    content = """
[[tool.poetry.source]]
name = "my-index"
url = "https://example.com/simple/"
priority = "unknown-value"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 1
    assert sources[0].priority is None


def test_source_without_name_is_skipped():
    content = """
[[tool.poetry.source]]
url = "https://example.com/simple/"
priority = "primary"

[[tool.poetry.source]]
name = "valid-index"
url = "https://valid.example.com/simple/"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 1
    assert sources[0].name == "valid-index"


def test_source_url_only():
    content = """
[[tool.poetry.source]]
name = "my-index"
url = "https://example.com/simple/"
"""
    document = parse(content)
    sources = parse_sources_from_document(document)

    assert len(sources) == 1
    assert sources[0].url == "https://example.com/simple/"
    assert sources[0].priority is None

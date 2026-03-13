import os
from unittest.mock import patch

from ps.version import Version

from .conftest import resolve


def test_version_resolver_literal_version(tmp_path):
    result = resolve(
        tmp_path,
        project_patterns=["{v:3.5.1}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("3.5.1")


def test_version_resolver_major_accessor(tmp_path):
    result = resolve(
        tmp_path,
        project_patterns=["{v:4.2.7:major}.0.0"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("4.0.0")


def test_version_resolver_minor_accessor(tmp_path):
    result = resolve(
        tmp_path,
        project_patterns=["0.{v:4.2.7:minor}.0"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.2.0")


def test_version_resolver_patch_accessor(tmp_path):
    result = resolve(
        tmp_path,
        project_patterns=["0.0.{v:4.2.7:patch}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.0.7")


def test_version_resolver_from_env_via_nested_expression(tmp_path):
    with patch.dict(os.environ, {"SOME": "6.3.2"}):
        result = resolve(
            tmp_path,
            project_patterns=["{v:{env:SOME}:major}.0.0"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("6.0.0")


def test_version_resolver_invalid_falls_through_to_next_pattern(tmp_path):
    result = resolve(
        tmp_path,
        project_version="2.0.0",
        project_patterns=["[{v:bad}] {v:bad}", "{spec}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("2.0.0")

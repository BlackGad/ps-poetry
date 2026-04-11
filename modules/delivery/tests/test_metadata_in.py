from ps.version import Version

from .conftest import resolve


def test_in_resolves_when_provided(tmp_path):
    result = resolve(
        tmp_path,
        input_version=Version.parse("5.0.0"),
        project_patterns=["[{in}] {in}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("5.0.0")


def test_in_condition_false_when_input_is_none(tmp_path):
    result = resolve(
        tmp_path,
        input_version=None,
        project_version="2.0.0",
        project_patterns=["[{in}] {in}", "{spec}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("2.0.0")


def test_in_major_accessor(tmp_path):
    result = resolve(
        tmp_path,
        input_version=Version.parse("7.3.1"),
        project_patterns=["{in:major}.0.0"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("7.0.0")


def test_in_minor_accessor(tmp_path):
    result = resolve(
        tmp_path,
        input_version=Version.parse("7.3.1"),
        project_patterns=["0.{in:minor}.0"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.3.0")


def test_in_patch_accessor(tmp_path):
    result = resolve(
        tmp_path,
        input_version=Version.parse("7.3.1"),
        project_patterns=["0.0.{in:patch}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.0.1")


def test_in_fallback_used_when_field_is_none(tmp_path):
    result = resolve(
        tmp_path,
        input_version=Version(major=1, minor=2, patch=3),
        project_patterns=["{in:major}.{in:minor}.{in:patch}.{in:rev<0>}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("1.2.3.0")

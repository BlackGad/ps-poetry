from ps.version import Version

from .conftest import resolve


def test_spec_resolves_project_version(tmp_path):
    result = resolve(tmp_path, project_version="3.5.1", project_patterns=["{spec}"])
    versions = list(result.projects.values())
    assert len(versions) == 1
    assert versions[0].version == Version.parse("3.5.1")


def test_spec_major_accessor(tmp_path):
    result = resolve(tmp_path, project_version="4.7.2", project_patterns=["{spec:major}.0.0"])
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("4.0.0")


def test_spec_minor_accessor(tmp_path):
    result = resolve(tmp_path, project_version="4.7.2", project_patterns=["0.{spec:minor}.0"])
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.7.0")


def test_spec_patch_accessor(tmp_path):
    result = resolve(tmp_path, project_version="4.7.2", project_patterns=["0.0.{spec:patch}"])
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.0.2")


def test_spec_fallback_to_host_when_project_version_is_zero(tmp_path):
    result = resolve(
        tmp_path,
        project_version="0.0.0",
        host_version="9.9.9",
        project_patterns=["{spec}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("9.9.9")


def test_spec_condition_is_truthy(tmp_path):
    result = resolve(
        tmp_path,
        project_version="2.0.0",
        project_patterns=["[{spec}] {spec}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("2.0.0")

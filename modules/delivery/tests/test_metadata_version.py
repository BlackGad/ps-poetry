import os
from unittest.mock import patch

from ps.version import Version, VersionStandard

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


def test_version_resolver_format_pep440_with_prerelease(tmp_path):
    # PEP440 renders pre-release as "1.2.3a1"
    result = resolve(
        tmp_path,
        project_patterns=["{v:1.2.3a1:format:pep440}"],
    )
    versions = list(result.projects.values())
    assert str(versions[0].version.format(VersionStandard.PEP440)) == "1.2.3a1"


def test_version_resolver_format_pep440_with_post(tmp_path):
    # PEP440 renders post as "1.2.3.post2"
    result = resolve(
        tmp_path,
        project_patterns=["{v:1.2.3.post2:format:pep440}"],
    )
    versions = list(result.projects.values())
    assert str(versions[0].version.format(VersionStandard.PEP440)) == "1.2.3.post2"


def test_version_resolver_format_semver_with_prerelease(tmp_path):
    # SemVer renders pre-release as "1.2.3-rc.1"
    result = resolve(
        tmp_path,
        project_patterns=["{v:1.2.3rc1:format:semver}"],
    )
    versions = list(result.projects.values())
    assert str(versions[0].version.format(VersionStandard.SEMVER)) == "1.2.3-rc.1"


def test_version_resolver_format_nuget_with_rev(tmp_path):
    # NuGet includes the rev field — "1.2.3.4"
    result = resolve(
        tmp_path,
        project_patterns=["{v:1.2.3.4:format:nuget}"],
    )
    versions = list(result.projects.values())
    assert str(versions[0].version.format(VersionStandard.NUGET)) == "1.2.3.4"


def test_version_resolver_format_calver_with_year(tmp_path):
    # CalVer uses major as the year — "2025.3.0"
    result = resolve(
        tmp_path,
        project_patterns=["{v:2025.3.0:format:calver}"],
    )
    versions = list(result.projects.values())
    assert str(versions[0].version.format(VersionStandard.CALVER)) == "2025.3.0"


def test_version_resolver_format_loose_simple(tmp_path):
    # Loose drops pre/post/dev — just core "1.2.3"
    result = resolve(
        tmp_path,
        project_patterns=["{v:1.2.3:format:loose}"],
    )
    versions = list(result.projects.values())
    assert str(versions[0].version.format(VersionStandard.LOOSE)) == "1.2.3"

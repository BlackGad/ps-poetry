import os
from unittest.mock import patch

from ps.version import Version

from ps.plugin.module.delivery.stages._metadata import _split_version_pattern

from .conftest import resolve


# ---------------------------------------------------------------------------
# _split_version_pattern
# ---------------------------------------------------------------------------


def test_split_pattern_with_condition():
    condition, version = _split_version_pattern("[{in}] {in}")
    assert condition == "{in}"
    assert version == "{in}"


def test_split_pattern_without_condition():
    condition, version = _split_version_pattern("{spec}")
    assert condition is None
    assert version == "{spec}"


def test_split_pattern_env_condition():
    condition, version = _split_version_pattern("[{env:BUILD_VERSION}] {env:BUILD_VERSION}")
    assert condition == "{env:BUILD_VERSION}"
    assert version == "{env:BUILD_VERSION}"


# ---------------------------------------------------------------------------
# Default pattern sequence: in → env:BUILD_VERSION → spec
# ---------------------------------------------------------------------------


def test_default_patterns_use_in_first(tmp_path):
    result = resolve(tmp_path, input_version=Version.parse("2.0.0"))
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("2.0.0")


def test_default_patterns_fall_through_to_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "BUILD_VERSION"}
    with patch.dict(os.environ, {**env, "BUILD_VERSION": "4.0.0"}, clear=True):
        result = resolve(tmp_path, input_version=None, project_version="1.0.0")
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("4.0.0")


def test_default_patterns_fall_through_to_spec(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "BUILD_VERSION"}
    with patch.dict(os.environ, env, clear=True):
        result = resolve(tmp_path, input_version=None, project_version="3.1.0")
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("3.1.0")


# ---------------------------------------------------------------------------
# Pattern priority: project overrides host
# ---------------------------------------------------------------------------


def test_project_patterns_override_host_patterns(tmp_path):
    result = resolve(
        tmp_path,
        host_patterns=["{spec}"],
        project_patterns=["[{in}] {in}"],
        input_version=Version.parse("9.0.0"),
        project_version="1.0.0",
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("9.0.0")


def test_host_patterns_used_when_project_has_none(tmp_path):
    result = resolve(
        tmp_path,
        host_patterns=["[{in}] {in}", "{spec}"],
        project_patterns=None,
        input_version=None,
        project_version="7.0.0",
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("7.0.0")


# ---------------------------------------------------------------------------
# Multiple patterns — first match wins
# ---------------------------------------------------------------------------


def test_first_matching_pattern_is_used(tmp_path):
    result = resolve(
        tmp_path,
        input_version=Version.parse("1.0.0"),
        project_version="2.0.0",
        project_patterns=["[{in}] {in}", "{spec}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("1.0.0")


def test_skips_to_next_pattern_when_condition_false(tmp_path):
    result = resolve(
        tmp_path,
        input_version=None,
        project_version="2.0.0",
        project_patterns=["[{in}] {in}", "{spec}"],
    )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("2.0.0")

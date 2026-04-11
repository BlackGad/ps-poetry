import os
from unittest.mock import patch

from ps.version import Version

from .conftest import resolve


def test_env_ver_resolves_when_var_set(tmp_path):
    with patch.dict(os.environ, {"BUILD_VERSION": "8.1.0"}):
        result = resolve(
            tmp_path,
            project_patterns=["[{env:BUILD_VERSION}] {v:{env:BUILD_VERSION}}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("8.1.0")


def test_env_ver_condition_false_when_var_missing(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "BUILD_VERSION"}
    with patch.dict(os.environ, env, clear=True):
        result = resolve(
            tmp_path,
            project_version="1.5.0",
            project_patterns=["[{env:BUILD_VERSION}] {v:{env:BUILD_VERSION}}", "{spec}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("1.5.0")


def test_env_ver_var_not_a_version_produces_default(tmp_path):
    with patch.dict(os.environ, {"BUILD_VERSION": "not-a-version"}):
        result = resolve(
            tmp_path,
            project_version="2.0.0",
            project_patterns=["[{env:BUILD_VERSION}] {v:{env:BUILD_VERSION}}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version()


def test_env_ver_major_accessor(tmp_path):
    with patch.dict(os.environ, {"BUILD_VERSION": "6.4.2"}):
        result = resolve(
            tmp_path,
            project_patterns=["{v:{env:BUILD_VERSION}:major}.0.0"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("6.0.0")


def test_env_ver_minor_accessor(tmp_path):
    with patch.dict(os.environ, {"BUILD_VERSION": "6.4.2"}):
        result = resolve(
            tmp_path,
            project_patterns=["0.{v:{env:BUILD_VERSION}:minor}.0"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.4.0")


def test_env_ver_patch_accessor(tmp_path):
    with patch.dict(os.environ, {"BUILD_VERSION": "6.4.2"}):
        result = resolve(
            tmp_path,
            project_patterns=["0.0.{v:{env:BUILD_VERSION}:patch}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("0.0.2")


def test_env_ver_custom_var_name(tmp_path):
    with patch.dict(os.environ, {"MY_VER": "3.1.0"}):
        result = resolve(
            tmp_path,
            project_patterns=["[{env:MY_VER}] {v:{env:MY_VER}}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("3.1.0")


def test_env_ver_missing_falls_through_to_next_pattern(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "MISSING_VAR"}
    with patch.dict(os.environ, env, clear=True):
        result = resolve(
            tmp_path,
            project_version="5.0.0",
            project_patterns=["[{env:MISSING_VAR}] {v:{env:MISSING_VAR}}", "{spec}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("5.0.0")

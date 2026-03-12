import os
from unittest.mock import patch

from ps.version import Version

from .conftest import resolve


def test_env_resolves_when_var_set(tmp_path):
    with patch.dict(os.environ, {"BUILD_VERSION": "8.1.0"}):
        result = resolve(
            tmp_path,
            project_patterns=["[{env:BUILD_VERSION}] {env:BUILD_VERSION}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("8.1.0")


def test_env_condition_false_when_var_missing(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "BUILD_VERSION"}
    with patch.dict(os.environ, env, clear=True):
        result = resolve(
            tmp_path,
            project_version="1.5.0",
            project_patterns=["[{env:BUILD_VERSION}] {env:BUILD_VERSION}", "{spec}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("1.5.0")


def test_env_custom_var_name(tmp_path):
    with patch.dict(os.environ, {"MY_VER": "3.0.0"}):
        result = resolve(
            tmp_path,
            project_patterns=["[{env:MY_VER}] {env:MY_VER}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("3.0.0")


def test_env_missing_falls_through_to_next_pattern(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "MISSING_VAR"}
    with patch.dict(os.environ, env, clear=True):
        result = resolve(
            tmp_path,
            project_version="5.0.0",
            project_patterns=["[{env:MISSING_VAR}] {env:MISSING_VAR}", "{spec}"],
        )
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("5.0.0")

from typing import Any
from unittest.mock import MagicMock

import pytest
import tomlkit

from ps.plugin.core.commands._enable import (
    DisableCommand,
    EnableCommand,
    _ensure_ps_plugin_section,
)


@pytest.fixture
def make_command():
    def _factory(cls, toml_str):
        document = tomlkit.parse(toml_str)
        pyproject = MagicMock()
        pyproject.data = document
        app = MagicMock()
        app.poetry.pyproject = pyproject
        cmd = cls(app)
        cmd.line = MagicMock()
        return cmd, document, pyproject
    return _factory


# --- _ensure_ps_plugin_section ---


def test_ensure_creates_tool_and_ps_plugin_when_missing():
    document = tomlkit.parse("")
    section = _ensure_ps_plugin_section(document)
    assert "tool" in document
    tool: Any = document["tool"]
    assert "ps-plugin" in tool
    assert list(section["modules"]) == []


def test_ensure_creates_ps_plugin_when_tool_exists():
    document = tomlkit.parse("[tool]\n")
    section = _ensure_ps_plugin_section(document)
    tool: Any = document["tool"]
    assert "ps-plugin" in tool
    assert list(section["modules"]) == []


def test_ensure_preserves_existing_ps_plugin():
    document = tomlkit.parse('[tool.ps-plugin]\nmodules = ["foo"]\n')
    section = _ensure_ps_plugin_section(document)
    assert list(section["modules"]) == ["foo"]


def test_ensure_preserves_existing_enabled_false():
    document = tomlkit.parse("[tool.ps-plugin]\nenabled = false\n")
    section = _ensure_ps_plugin_section(document)
    assert not bool(section["enabled"])


# --- EnableCommand ---


def test_enable_removes_enabled_false(make_command):
    cmd, document, pyproject = make_command(
        EnableCommand, "[tool.ps-plugin]\nenabled = false\nmodules = []\n"
    )
    result = cmd.handle()
    assert result == 0
    assert "enabled" not in document["tool"]["ps-plugin"]
    pyproject.save.assert_called_once()
    cmd.line.assert_called_once()
    assert "Removed" in cmd.line.call_args[0][0]


def test_enable_already_enabled_no_enabled_key(make_command):
    cmd, document, pyproject = make_command(
        EnableCommand, '[tool.ps-plugin]\nmodules = ["x"]\n'
    )
    result = cmd.handle()
    assert result == 0
    assert "enabled" not in document["tool"]["ps-plugin"]
    pyproject.save.assert_called_once()
    cmd.line.assert_called_once()
    assert "already enabled" in cmd.line.call_args[0][0]


def test_enable_already_enabled_with_enabled_true(make_command):
    cmd, _document, pyproject = make_command(
        EnableCommand, "[tool.ps-plugin]\nenabled = true\nmodules = []\n"
    )
    result = cmd.handle()
    assert result == 0
    pyproject.save.assert_called_once()
    cmd.line.assert_called_once()
    assert "already enabled" in cmd.line.call_args[0][0]


def test_enable_creates_section_when_missing(make_command):
    cmd, document, pyproject = make_command(EnableCommand, "")
    result = cmd.handle()
    assert result == 0
    assert "tool" in document
    assert "ps-plugin" in document["tool"]
    pyproject.save.assert_called_once()
    assert "already enabled" in cmd.line.call_args[0][0]


# --- DisableCommand ---


def test_disable_sets_enabled_false(make_command):
    cmd, document, pyproject = make_command(
        DisableCommand, "[tool.ps-plugin]\nmodules = []\n"
    )
    result = cmd.handle()
    assert result == 0
    assert not bool(document["tool"]["ps-plugin"]["enabled"])
    pyproject.save.assert_called_once()
    cmd.line.assert_called_once()
    assert "Set" in cmd.line.call_args[0][0]


def test_disable_already_disabled(make_command):
    cmd, document, pyproject = make_command(
        DisableCommand, "[tool.ps-plugin]\nenabled = false\nmodules = []\n"
    )
    result = cmd.handle()
    assert result == 0
    assert not bool(document["tool"]["ps-plugin"]["enabled"])
    pyproject.save.assert_called_once()
    cmd.line.assert_called_once()
    assert "already disabled" in cmd.line.call_args[0][0]


def test_disable_creates_section_when_missing(make_command):
    cmd, document, pyproject = make_command(DisableCommand, "")
    result = cmd.handle()
    assert result == 0
    assert "tool" in document
    assert "ps-plugin" in document["tool"]
    assert not bool(document["tool"]["ps-plugin"]["enabled"])
    pyproject.save.assert_called_once()


def test_disable_overwrites_enabled_true(make_command):
    cmd, document, pyproject = make_command(
        DisableCommand, "[tool.ps-plugin]\nenabled = true\nmodules = []\n"
    )
    result = cmd.handle()
    assert result == 0
    assert not bool(document["tool"]["ps-plugin"]["enabled"])
    pyproject.save.assert_called_once()
    assert "Set" in cmd.line.call_args[0][0]

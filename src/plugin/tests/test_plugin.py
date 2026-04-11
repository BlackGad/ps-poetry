import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity
from poetry.console.application import Application

from ps.di import DI
from ps.plugin.core._plugin import (
    Plugin,
    _activate_project_venv,
    _create_standard_io,
    _resolve_settings,
)
from ps.plugin.sdk.project import Environment
from ps.plugin.sdk.settings import PluginSettings

_PATCH_BASE = "ps.plugin.core._plugin"


# --- _create_standard_io ---


def test_create_standard_io_returns_io():
    io = _create_standard_io()
    assert isinstance(io, IO)


def test_create_standard_io_has_debug_verbosity():
    io = _create_standard_io()
    assert io.output.verbosity == Verbosity.DEBUG
    assert io.error_output.verbosity == Verbosity.DEBUG


# --- _activate_project_venv ---


@pytest.fixture
def mock_io():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    return io


@pytest.fixture
def mock_app():
    app = MagicMock(spec=Application)
    return app


def test_activate_venv_skips_when_virtual_env_set(mock_app, mock_io, monkeypatch):
    monkeypatch.setenv("VIRTUAL_ENV", "/some/venv")
    monkeypatch.delenv("CONDA_DEFAULT_ENV", raising=False)
    _activate_project_venv(mock_app, mock_io)


def test_activate_venv_skips_when_conda_prefix_set(mock_app, mock_io, monkeypatch):
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.setenv("CONDA_PREFIX", "/some/conda")
    monkeypatch.delenv("CONDA_DEFAULT_ENV", raising=False)
    _activate_project_venv(mock_app, mock_io)


def test_activate_venv_skips_base_conda_env(mock_app, mock_io, monkeypatch):
    monkeypatch.setenv("CONDA_PREFIX", "/some/conda")
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "base")
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    with patch(f"{_PATCH_BASE}.EnvManager") as env_mgr_cls:
        env_mgr_cls.return_value.get.side_effect = Exception("fail")
        _activate_project_venv(mock_app, mock_io)
        env_mgr_cls.assert_called_once()


def test_activate_venv_skips_when_env_resolution_fails(mock_app, mock_io, monkeypatch):
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    with patch(f"{_PATCH_BASE}.EnvManager") as env_mgr_cls:
        env_mgr_cls.return_value.get.side_effect = RuntimeError("no env")
        _activate_project_venv(mock_app, mock_io)


def test_activate_venv_skips_when_path_does_not_exist(mock_app, mock_io, monkeypatch):
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    mock_env = MagicMock()
    mock_env.path = Path("/nonexistent/venv")
    with patch(f"{_PATCH_BASE}.EnvManager") as env_mgr_cls:
        env_mgr_cls.return_value.get.return_value = mock_env
        _activate_project_venv(mock_app, mock_io)


def test_activate_venv_skips_when_site_packages_missing(mock_app, mock_io, tmp_path, monkeypatch):
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    mock_env = MagicMock()
    mock_env.path = tmp_path
    with patch(f"{_PATCH_BASE}.EnvManager") as env_mgr_cls:
        env_mgr_cls.return_value.get.return_value = mock_env
        _activate_project_venv(mock_app, mock_io)


def test_activate_venv_adds_site_packages_and_bin(mock_app, mock_io, tmp_path, monkeypatch):
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)

    if sys.platform == "win32":
        site_pkgs = tmp_path / "Lib" / "site-packages"
        bin_dir = tmp_path / "Scripts"
    else:
        py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        site_pkgs = tmp_path / "lib" / py_ver / "site-packages"
        bin_dir = tmp_path / "bin"

    site_pkgs.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    mock_env = MagicMock()
    mock_env.path = tmp_path

    original_path = os.environ.get("PATH", "")
    with patch(f"{_PATCH_BASE}.EnvManager") as env_mgr_cls, \
            patch(f"{_PATCH_BASE}.site") as mock_site:
        env_mgr_cls.return_value.get.return_value = mock_env
        _activate_project_venv(mock_app, mock_io)
        mock_site.addsitedir.assert_called_once_with(str(site_pkgs))

    assert str(bin_dir) in os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", original_path)


# --- _resolve_settings ---


def test_resolve_settings_returns_host_project_settings():
    env = MagicMock(spec=Environment)
    settings = PluginSettings(enabled=True)
    env.host_project.plugin_settings = settings
    result = _resolve_settings(env)
    assert result is settings


# --- Plugin.__init__ ---


def test_plugin_init_creates_di():
    plugin = Plugin()
    assert isinstance(plugin._di, DI)


# --- Plugin._ensure_io ---


def test_ensure_io_returns_existing_io():
    plugin = Plugin()
    app = MagicMock(spec=Application)
    existing_io = MagicMock(spec=IO)
    app._io = existing_io
    result = plugin._ensure_io(app)
    assert result is existing_io


def test_ensure_io_creates_io_when_missing():
    plugin = Plugin()
    app = MagicMock(spec=Application)
    del app._io  # make getattr return None
    with patch(f"{_PATCH_BASE}._create_standard_io") as mock_create:
        mock_io = MagicMock(spec=IO)
        mock_create.return_value = mock_io
        result = plugin._ensure_io(app)
        assert result is mock_io
        assert app._io is mock_io


# --- Plugin.activate ---


def _make_application(toml_data, *, pyproject_path=None, dispatcher=None):
    app = MagicMock(spec=Application)
    app.poetry.pyproject.data = toml_data
    app.poetry.pyproject_path = pyproject_path or Path("/fake/pyproject.toml")
    app.poetry.pyproject.file = Path("/fake/pyproject.toml")
    app.event_dispatcher = dispatcher or MagicMock(spec=EventDispatcher)
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    app._io = io
    return app


def test_activate_returns_early_when_disabled():
    plugin = Plugin()
    app = _make_application({})
    with patch(f"{_PATCH_BASE}.parse_plugin_settings_from_document") as mock_parse:
        mock_parse.return_value = PluginSettings(enabled=False)
        plugin.activate(app)
    assert not hasattr(plugin, "poetry")


def test_activate_returns_early_on_parse_error():
    plugin = Plugin()
    app = _make_application({})
    with patch(f"{_PATCH_BASE}.parse_plugin_settings_from_document") as mock_parse:
        mock_parse.side_effect = Exception("bad toml")
        plugin.activate(app)
    assert not hasattr(plugin, "poetry")


def test_activate_successful_flow():
    plugin = Plugin()
    dispatcher = MagicMock(spec=EventDispatcher)
    app = _make_application({}, dispatcher=dispatcher)
    settings = PluginSettings(enabled=True, modules=[])

    with patch(f"{_PATCH_BASE}.parse_plugin_settings_from_document", return_value=settings), \
            patch(f"{_PATCH_BASE}._activate_project_venv"), \
            patch(f"{_PATCH_BASE}.Environment"), \
            patch(f"{_PATCH_BASE}._resolve_settings", return_value=settings):
        mock_handler = MagicMock()
        mock_handler.get_event_handlers.return_value = []
        plugin._di.spawn = MagicMock(return_value=mock_handler)

        plugin.activate(app)

    assert plugin.poetry is app.poetry
    mock_handler.discover_and_instantiate.assert_called_once()
    mock_handler.activate.assert_called_once()


def test_activate_registers_event_listeners():
    plugin = Plugin()
    dispatcher = MagicMock(spec=EventDispatcher)
    app = _make_application({}, dispatcher=dispatcher)
    settings = PluginSettings(enabled=True, modules=[])

    handler_fn = MagicMock()

    with patch(f"{_PATCH_BASE}.parse_plugin_settings_from_document", return_value=settings), \
            patch(f"{_PATCH_BASE}._activate_project_venv"), \
            patch(f"{_PATCH_BASE}.Environment"), \
            patch(f"{_PATCH_BASE}._resolve_settings", return_value=settings):
        mock_handler = MagicMock()
        mock_handler.get_event_handlers.side_effect = lambda et: [handler_fn] if et == "command" else []
        plugin._di.spawn = MagicMock(return_value=mock_handler)

        plugin.activate(app)

    assert dispatcher.add_listener.call_count == 1


# --- Plugin._register_listener ---


def test_register_listener_calls_handlers_in_scope():
    plugin = Plugin()
    di = DI()
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    dispatcher = MagicMock(spec=EventDispatcher)

    called = []

    def handler_fn():
        called.append(True)

    di.register(IO).factory(lambda: io)
    plugin._register_listener(dispatcher, di, io, "command", "console.command", [handler_fn])

    assert dispatcher.add_listener.call_count == 1
    event_constant, listener_fn = dispatcher.add_listener.call_args[0]
    assert event_constant == "console.command"

    event = MagicMock(spec=ConsoleCommandEvent)
    event.command_should_run.return_value = True
    listener_fn(event, "console.command", dispatcher)

    assert len(called) == 1


def test_register_listener_stops_on_command_should_not_run():
    plugin = Plugin()
    di = DI()
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    dispatcher = MagicMock(spec=EventDispatcher)

    call_order = []

    def handler1():
        call_order.append("h1")

    def handler2():
        call_order.append("h2")

    di.register(IO).factory(lambda: io)
    plugin._register_listener(dispatcher, di, io, "command", "console.command", [handler1, handler2])

    _, listener_fn = dispatcher.add_listener.call_args[0]

    event = MagicMock(spec=ConsoleCommandEvent)
    event.command_should_run.side_effect = [False]
    listener_fn(event, "console.command", dispatcher)

    assert call_order == ["h1"]

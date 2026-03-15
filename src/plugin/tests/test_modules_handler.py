from unittest.mock import MagicMock, patch

from cleo.io.io import IO

from ps.di import DI
from ps.plugin.core._modules_handler import (
    _ModuleInfo,
    _ModulesHandler,
    _detect_collisions,
    _scan_class,
    _scan_function,
)
from ps.plugin.sdk.settings import PluginSettings

_PATCH_TARGET = "ps.plugin.core._modules_handler._load_module_infos"


def _make_di(modules: list[str] | None) -> DI:
    di = DI()
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    di.register(IO).factory(lambda: io)
    di.register(PluginSettings).factory(lambda: PluginSettings(modules=modules))
    return di


def _activate_true():
    return True


def _activate_false():
    return False


def _activate_none():
    return None


def _info(name: str, event_types: list[str], *, activate_fn: object = _activate_true, distribution: str | None = "test-dist") -> _ModuleInfo:
    handlers: dict = {}
    for et in event_types:
        handlers[et] = activate_fn if et == "activate" else MagicMock()
    return _ModuleInfo(name=name, handlers=handlers, distribution=distribution)


# --- discover_and_instantiate ---


def test_no_modules_when_setting_is_none():
    di = _make_di(modules=None)
    handler = di.spawn(_ModulesHandler)
    infos = [_info("mod-a", ["activate", "command"])]

    with patch(_PATCH_TARGET, return_value=infos):
        handler.discover_and_instantiate()

    assert handler.get_module_names() == []
    assert handler.get_event_handlers("activate") == []
    assert handler.get_event_handlers("command") == []


def test_specified_modules_are_loaded():
    di = _make_di(modules=["mod-a"])
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["activate", "command"])
    info_b = _info("mod-b", ["command"])

    with patch(_PATCH_TARGET, return_value=[info_a, info_b]):
        handler.discover_and_instantiate()

    assert handler.get_module_names() == ["mod-a"]
    assert handler.get_event_handlers("command") == [info_a.handlers["command"]]


def test_unrecognised_module_names_are_ignored():
    di = _make_di(modules=["nonexistent"])
    handler = di.spawn(_ModulesHandler)
    infos = [_info("mod-a", ["command"])]

    with patch(_PATCH_TARGET, return_value=infos):
        handler.discover_and_instantiate()

    assert handler.get_module_names() == []
    assert handler.get_event_handlers("command") == []


def test_modules_loaded_in_declared_order():
    di = _make_di(modules=["mod-b", "mod-a"])
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["command"])
    info_b = _info("mod-b", ["command"])

    with patch(_PATCH_TARGET, return_value=[info_a, info_b]):
        handler.discover_and_instantiate()

    assert handler.get_module_names() == ["mod-b", "mod-a"]
    assert handler.get_event_handlers("command") == [
        info_b.handlers["command"],
        info_a.handlers["command"],
    ]


# --- collision detection ---


def test_collision_removes_all_conflicting_and_warns():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = True
    io.is_debug.return_value = False
    mod1 = _ModuleInfo(name="colliding", handlers={}, distribution="dist-a")
    mod2 = _ModuleInfo(name="colliding", handlers={}, distribution="dist-b")
    mod_safe = _ModuleInfo(name="safe", handlers={}, distribution="dist-c")

    result = _detect_collisions([mod1, mod2, mod_safe], io)

    assert [m.name for m in result] == ["safe"]
    io.write_line.assert_called_once()


# --- activate ---


def test_activate_false_disables_module():
    di = _make_di(modules=["mod-a"])
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["activate", "command"], activate_fn=_activate_false)

    with patch(_PATCH_TARGET, return_value=[info_a]):
        handler.discover_and_instantiate()
        handler.activate()

    assert handler.get_module_names() == []
    assert handler.get_event_handlers("command") == []


def test_activate_true_keeps_module_active():
    di = _make_di(modules=["mod-a"])
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["activate", "command"], activate_fn=_activate_true)

    with patch(_PATCH_TARGET, return_value=[info_a]):
        handler.discover_and_instantiate()
        handler.activate()

    assert handler.get_module_names() == ["mod-a"]
    assert handler.get_event_handlers("command") == [info_a.handlers["command"]]


def test_activate_none_keeps_module_active():
    di = _make_di(modules=["mod-a"])
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["activate", "command"], activate_fn=_activate_none)

    with patch(_PATCH_TARGET, return_value=[info_a]):
        handler.discover_and_instantiate()
        handler.activate()

    assert handler.get_module_names() == ["mod-a"]
    assert handler.get_event_handlers("command") == [info_a.handlers["command"]]


# --- scan_class ---


class _SampleModule:
    name = "sample"

    def poetry_activate(self, application):
        pass

    def poetry_command(self, event):
        pass


class _NoNameModule:
    def poetry_command(self, event):
        pass


def test_scan_class_extracts_handlers():
    modules = _scan_class(_SampleModule, "test-dist")
    assert len(modules) == 1
    assert modules[0].name == "sample"
    assert set(modules[0].handlers.keys()) == {"activate", "command"}


def test_scan_class_falls_back_to_class_name():
    modules = _scan_class(_NoNameModule, "test-dist")
    assert len(modules) == 1
    assert modules[0].name == "_NoNameModule"


# --- scan_function ---


def poetry_command_mymod():
    pass


def poetry_command():
    pass


def not_a_handler():
    pass


def test_scan_function_with_suffix():
    result = _scan_function(poetry_command_mymod, "test-dist")
    assert result is not None
    assert result.name == "mymod"
    assert "command" in result.handlers


def test_scan_function_without_suffix_rejected():
    result = _scan_function(poetry_command, "test-dist")
    assert result is None


def test_scan_function_non_matching_rejected():
    result = _scan_function(not_a_handler, "test-dist")
    assert result is None

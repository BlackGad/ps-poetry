from unittest.mock import MagicMock, patch

import pytest
from cleo.io.io import IO

from ps.di import DI
from ps.plugin.core._modules_handler import (
    _ModuleInfo,
    _ModulesHandler,
    _detect_collisions,
    _event_to_method_name,
    _get_class_name,
    _get_defining_class,
    _get_distribution,
    _get_module_path,
    _is_static_or_classmethod,
    _is_unbound_method,
    _load_module_infos,
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


def test_duplicate_scan_same_path_picks_first():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    mod1 = _ModuleInfo(name="dup", handlers={}, distribution="dist-a", path="/some/module.py")
    mod2 = _ModuleInfo(name="dup", handlers={}, distribution="dist-b", path="/some/module.py")
    mod_safe = _ModuleInfo(name="safe", handlers={}, distribution="dist-c", path="/other/module.py")

    result = _detect_collisions([mod1, mod2, mod_safe], io)

    assert [m.name for m in result] == ["dup", "safe"]
    assert result[0] is mod1
    io.write_line.assert_not_called()


def test_duplicate_scan_none_paths_treated_as_collision():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = True
    io.is_debug.return_value = False
    mod1 = _ModuleInfo(name="ambiguous", handlers={}, distribution="dist-a", path=None)
    mod2 = _ModuleInfo(name="ambiguous", handlers={}, distribution="dist-b", path=None)

    result = _detect_collisions([mod1, mod2], io)

    assert result == []
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


# --- _scan_class: static/class methods ---


class _StaticMethodModule:
    name = "static_mod"

    @staticmethod
    def poetry_command_extra():
        pass

    @classmethod
    def poetry_activate_extra(cls):
        pass


class _StaticMethodNoSuffix:
    name = "nosuffix"

    @staticmethod
    def poetry_command():
        pass


class _MixedModule:
    name = "mixed"

    def poetry_activate(self, app):
        pass

    @staticmethod
    def poetry_command_helper():
        pass


def test_scan_class_static_methods_with_suffix():
    modules = _scan_class(_StaticMethodModule, "dist")
    names = {m.name for m in modules}
    assert "extra" in names
    extra = next(m for m in modules if m.name == "extra")
    assert set(extra.handlers.keys()) == {"command", "activate"}


def test_scan_class_static_method_without_suffix_ignored():
    modules = _scan_class(_StaticMethodNoSuffix, "dist")
    assert len(modules) == 0


def test_scan_class_mixed_instance_and_static():
    modules = _scan_class(_MixedModule, "dist")
    names = {m.name for m in modules}
    assert "mixed" in names
    assert "helper" in names


# --- _get_module_path ---


def test_get_module_path_returns_path_for_class():
    path = _get_module_path(_SampleModule)
    assert path is not None
    assert path.endswith(".py")


def test_get_module_path_returns_none_for_builtin():
    result = _get_module_path(int)
    assert result is None


# --- _get_distribution ---


def test_get_distribution_returns_name():
    ep = MagicMock()
    ep.dist.name = "my-package"
    assert _get_distribution(ep) == "my-package"


def test_get_distribution_returns_none_when_no_dist():
    ep = MagicMock()
    ep.dist = None
    assert _get_distribution(ep) is None


def test_get_distribution_returns_none_on_exception():
    ep = MagicMock()
    type(ep).dist = property(lambda _self: (_ for _ in ()).throw(RuntimeError("fail")))
    assert _get_distribution(ep) is None


# --- _get_class_name ---


class _NamedClass:
    name = "custom"


class _UnnamedClass:
    pass


class _NonStringName:
    name = 42


def test_get_class_name_uses_name_attribute():
    assert _get_class_name(_NamedClass) == "custom"


def test_get_class_name_falls_back_to_class_name():
    assert _get_class_name(_UnnamedClass) == "_UnnamedClass"


def test_get_class_name_ignores_non_string_name():
    assert _get_class_name(_NonStringName) == "_NonStringName"


# --- _is_static_or_classmethod ---


class _MethodTypes:
    def instance_method(self):
        pass

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass


def test_is_static_or_classmethod_for_instance():
    assert _is_static_or_classmethod(_MethodTypes, "instance_method") is False


def test_is_static_or_classmethod_for_static():
    assert _is_static_or_classmethod(_MethodTypes, "static_method") is True


def test_is_static_or_classmethod_for_classmethod():
    assert _is_static_or_classmethod(_MethodTypes, "class_method") is True


def test_is_static_or_classmethod_nonexistent():
    assert _is_static_or_classmethod(_MethodTypes, "nonexistent") is False


# --- _is_unbound_method ---


def test_is_unbound_method_for_class_method():
    assert _is_unbound_method(_SampleModule.poetry_command) is True


def test_is_unbound_method_for_plain_function():
    assert _is_unbound_method(poetry_command_mymod) is False


def _module_level_lambda() -> None:
    pass


def test_is_unbound_method_for_module_level_function():
    assert _is_unbound_method(_module_level_lambda) is False


# --- _get_defining_class ---


def test_get_defining_class_for_unbound_method():
    cls = _get_defining_class(_SampleModule.poetry_command)
    assert cls is _SampleModule


def test_get_defining_class_for_plain_function():
    result = _get_defining_class(poetry_command_mymod)
    assert result is None


# --- _event_to_method_name ---


class _MethodNameModule:
    def poetry_activate(self):
        pass

    def poetry_command_mymod(self):
        pass


def test_event_to_method_name_base_exists():
    assert _event_to_method_name("activate", "mymod", _MethodNameModule) == "poetry_activate"


def test_event_to_method_name_falls_back_to_suffix():
    assert _event_to_method_name("command", "mymod", _MethodNameModule) == "poetry_command_mymod"


# --- _load_module_infos ---


def test_load_module_infos_loads_class_entry_point():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False

    ep = MagicMock()
    ep.group = "ps.module"
    ep.name = "test"
    ep.load.return_value = _SampleModule
    ep.dist.name = "test-dist"

    with patch("ps.plugin.core._modules_handler.metadata.entry_points", return_value=[ep]):
        modules = _load_module_infos(io)

    assert len(modules) == 1
    assert modules[0].name == "sample"


def test_load_module_infos_loads_function_entry_point():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False

    ep = MagicMock()
    ep.group = "ps.module"
    ep.name = "test"
    ep.load.return_value = poetry_command_mymod
    ep.dist.name = "test-dist"

    with patch("ps.plugin.core._modules_handler.metadata.entry_points", return_value=[ep]):
        modules = _load_module_infos(io)

    assert len(modules) == 1
    assert modules[0].name == "mymod"


def test_load_module_infos_skips_failed_entry_point():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False

    ep = MagicMock()
    ep.group = "ps.module"
    ep.name = "broken"
    ep.load.side_effect = ImportError("nope")

    with patch("ps.plugin.core._modules_handler.metadata.entry_points", return_value=[ep]):
        modules = _load_module_infos(io)

    assert modules == []


def test_load_module_infos_skips_unsupported_type():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = True
    io.is_debug.return_value = False

    ep = MagicMock()
    ep.group = "ps.module"
    ep.name = "weird"
    ep.load.return_value = 42
    ep.dist.name = "test-dist"

    with patch("ps.plugin.core._modules_handler.metadata.entry_points", return_value=[ep]):
        modules = _load_module_infos(io)

    assert modules == []


# --- discover_and_instantiate with verbose ---


def test_discover_verbose_logs_selected_and_unselected():
    di = _make_di(modules=["mod-a"])
    io = di.resolve(IO)
    assert io is not None
    io.is_verbose.return_value = True  # type: ignore[attr-defined]
    io.is_debug.return_value = False  # type: ignore[attr-defined]
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["command"])
    info_b = _info("mod-b", ["command"])

    with patch(_PATCH_TARGET, return_value=[info_a, info_b]):
        handler.discover_and_instantiate()

    write_calls = [str(c) for c in io.write_line.call_args_list]  # type: ignore[attr-defined]
    assert any("mod-a" in c for c in write_calls)
    assert any("mod-b" in c for c in write_calls)


def test_discover_debug_logs_module_paths():
    di = _make_di(modules=["mod-a"])
    io = di.resolve(IO)
    assert io is not None
    io.is_verbose.return_value = True  # type: ignore[attr-defined]
    io.is_debug.return_value = True  # type: ignore[attr-defined]
    handler = di.spawn(_ModulesHandler)
    info_a = _info("mod-a", ["command"])
    info_a.path = "/some/path.py"

    with patch(_PATCH_TARGET, return_value=[info_a]):
        handler.discover_and_instantiate()

    write_calls = [str(c) for c in io.write_line.call_args_list]  # type: ignore[attr-defined]
    assert any("/some/path.py" in c for c in write_calls)


# --- collision detection: debug logging ---


def test_collision_debug_shows_paths():
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = True
    io.is_debug.return_value = True
    mod1 = _ModuleInfo(name="dup", handlers={}, distribution="dist-a", path="/a.py")
    mod2 = _ModuleInfo(name="dup", handlers={}, distribution="dist-b", path="/b.py")

    _detect_collisions([mod1, mod2], io)

    write_calls = [str(c) for c in io.write_line.call_args_list]
    assert any("/a.py" in c for c in write_calls)
    assert any("/b.py" in c for c in write_calls)


# --- activate error handling ---


def test_activate_raises_on_handler_error():
    di = _make_di(modules=["mod-a"])
    handler = di.spawn(_ModulesHandler)

    def failing_activate():
        raise ValueError("boom")

    info_a = _info("mod-a", ["activate", "command"], activate_fn=failing_activate)

    with patch(_PATCH_TARGET, return_value=[info_a]):
        handler.discover_and_instantiate()
        with pytest.raises(ValueError, match="boom"):
            handler.activate()


# --- discover_and_instantiate with class-based modules ---


class _InstantiableModule:
    name = "inst"

    def __init__(self, io: IO) -> None:
        self.io = io

    def poetry_activate(self):
        return True

    def poetry_command(self):
        pass


def test_discover_instantiates_class_based_module():
    di = _make_di(modules=["inst"])
    handler = di.spawn(_ModulesHandler)
    modules = _scan_class(_InstantiableModule, "test-dist")

    with patch(_PATCH_TARGET, return_value=modules):
        handler.discover_and_instantiate()

    assert handler.get_module_names() == ["inst"]
    handlers = handler.get_event_handlers("command")
    assert len(handlers) == 1

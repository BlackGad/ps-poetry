from typing import List
from unittest.mock import MagicMock, patch

from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.io import IO
from poetry.console.application import Application

from ps.plugin.core._di import _DI
from ps.plugin.core._modules_handler import _ModulesHandler
from ps.plugin.sdk.di import DI
from ps.plugin.sdk.events import ActivateProtocol, ListenerCommandProtocol
from ps.plugin.sdk.settings import PluginSettings


def _make_di(modules: List[str] | None) -> DI:
    di = _DI()
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    di.register(IO).factory(lambda: io)
    di.register(PluginSettings).factory(lambda: PluginSettings(modules=modules))
    return di


class _ActivateModule:
    name = "activate-module"

    def handle_activate(self, application: Application) -> bool:
        return True


class _CommandModule:
    name = "command-module"

    def handle_command(self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher) -> None:
        pass


_FAKE_ENTRIES = [
    ("spec.activate", _ActivateModule),
    ("spec.command", _CommandModule),
]


def test_no_modules_loaded_when_modules_setting_is_absent():
    di = _make_di(modules=None)
    handler = _ModulesHandler(di)

    with patch("ps.plugin.core._modules_handler._load_module_class_types", return_value=_FAKE_ENTRIES):
        handler.instantiate_modules()

    assert handler.acquire_protocol_handlers(ActivateProtocol) == []
    assert handler.acquire_protocol_handlers(ListenerCommandProtocol) == []


def test_specified_modules_are_loaded():
    di = _make_di(modules=["activate-module"])
    handler = _ModulesHandler(di)

    with patch("ps.plugin.core._modules_handler._load_module_class_types", return_value=_FAKE_ENTRIES):
        handler.instantiate_modules()

    activate_handlers = handler.acquire_protocol_handlers(ActivateProtocol)
    command_handlers = handler.acquire_protocol_handlers(ListenerCommandProtocol)

    assert len(activate_handlers) == 1
    assert isinstance(activate_handlers[0], _ActivateModule)
    assert command_handlers == []


def test_unrecognised_module_names_are_ignored():
    di = _make_di(modules=["nonexistent-module"])
    handler = _ModulesHandler(di)

    with patch("ps.plugin.core._modules_handler._load_module_class_types", return_value=_FAKE_ENTRIES):
        handler.instantiate_modules()

    assert handler.acquire_protocol_handlers(ActivateProtocol) == []
    assert handler.acquire_protocol_handlers(ListenerCommandProtocol) == []


def test_modules_instantiated_in_declared_order():
    di = _make_di(modules=["command-module", "activate-module"])
    handler = _ModulesHandler(di)

    with patch("ps.plugin.core._modules_handler._load_module_class_types", return_value=_FAKE_ENTRIES):
        handler.instantiate_modules()

    activate_handlers = handler.acquire_protocol_handlers(ActivateProtocol)
    command_handlers = handler.acquire_protocol_handlers(ListenerCommandProtocol)

    assert len(activate_handlers) == 1
    assert isinstance(activate_handlers[0], _ActivateModule)
    assert len(command_handlers) == 1
    assert isinstance(command_handlers[0], _CommandModule)

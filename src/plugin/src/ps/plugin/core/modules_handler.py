from typing import Iterable, List, Type
import inspect
from importlib import metadata

from poetry.console.application import Application
from cleo.io.io import IO

from ps.plugin.sdk import (
    SetupProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    ListenerErrorProtocol,
    ListenerSignalProtocol,
    DI,
)
from .logging import _log_debug, _log_verbose


def _instantiate_module(module_type: Type, available_dependencies: dict[str, object]) -> object:
    sig = inspect.signature(module_type.__init__)
    kwargs = {}
    for param_name, _ in sig.parameters.items():
        if param_name == 'self':
            continue
        if param_name in available_dependencies:
            kwargs[param_name] = available_dependencies[param_name]
    return module_type(**kwargs)


def _load_module_class_types() -> Iterable[tuple[str, Type]]:
    module_entry_points = metadata.entry_points(group="ps.module")
    type_to_entry: dict[Type, str] = {}

    def add_type(module_type: Type, entry_spec: str) -> None:
        if module_type not in type_to_entry or len(entry_spec) > len(type_to_entry[module_type]):
            type_to_entry[module_type] = entry_spec

    for entry_point in module_entry_points:
        try:
            entry_spec = entry_point.value
            loaded_entry_point = entry_point.load()
            if inspect.isclass(loaded_entry_point):
                add_type(loaded_entry_point, entry_spec)
            elif inspect.ismodule(loaded_entry_point):
                for _, obj in inspect.getmembers(loaded_entry_point, inspect.isclass):
                    if obj.__module__.startswith(loaded_entry_point.__name__):
                        add_type(obj, entry_spec)
            elif inspect.isfunction(loaded_entry_point):
                raise TypeError("Module entry point cannot be a function.")
        except metadata.PackageNotFoundError:
            continue

    return [(entry_spec, module_type) for module_type, entry_spec in type_to_entry.items()]


class ModulesHandler:
    def __init__(self, di: DI) -> None:
        self._modules_instances: List[object] = []
        self._managed_protocols: dict[Type, List[object]] = {}
        self._di = di

    def instantiate_modules(self, application: Application) -> None:
        io = self._di.resolve(IO)
        assert io is not None

        module_entries = _load_module_class_types()
        module_types_list = [(entry_spec, module_type) for entry_spec, module_type in module_entries]
        if module_types_list:
            _log_verbose(io, f"Discovered {len(module_types_list)} module type(s)")
            for entry_spec, cls_name in module_types_list:
                _log_debug(io, f"  - <comment>{entry_spec}</comment> -> <fg=yellow>{cls_name.__name__}</>")
        else:
            _log_debug(io, "No module types discovered")

        protocols: List[Type] = [
            SetupProtocol,
            ListenerCommandProtocol,
            ListenerTerminateProtocol,
            ListenerErrorProtocol,
            ListenerSignalProtocol,
        ]

        unique_module_types = {module_type for _, module_type in module_types_list}

        for module_type in unique_module_types:
            # Get supported protocols for this module
            supported_protocols_by_module: List[Type] = [protocol for protocol in protocols if issubclass(module_type, protocol)]
            if not supported_protocols_by_module:
                # Module class does not support any known protocol
                continue
            _log_debug(io, f"Module <comment>{module_type.__name__}</comment> supports {len(supported_protocols_by_module)} protocol(s):")
            for protocol in supported_protocols_by_module:
                _log_debug(io, f"  - <fg=yellow>{protocol.__name__}</>")
            # Instantiate the module
            module_instance = _instantiate_module(
                module_type,
                {
                    "io": io,
                    "application": application,
                })
            self._modules_instances.append(module_instance)
            for protocol in supported_protocols_by_module:
                self._managed_protocols.setdefault(protocol, []).append(module_instance)

    def acquire_protocol_handlers[T](self, protocol: Type[T]) -> List[T]:
        return self._managed_protocols.get(protocol, [])  # type: ignore

    def is_protocol_managed(self, protocol: Type) -> bool:
        return protocol in self._managed_protocols

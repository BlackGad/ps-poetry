from typing import Iterable, List, Type
import inspect
from importlib import metadata

from cleo.io.io import IO

from .protocols import (
    ModuleProtocol,
    CustomProtocolsProtocol,
    GlobalSetupProtocol,
    CommandProtocol,
    TerminateProtocol,
    ErrorProtocol,
    SignalProtocol,
)


class ProtocolExecutionError(Exception):
    pass


def _load_module_types() -> Iterable[Type]:
    module_entry_points = metadata.entry_points(group="ps.module")
    module_types: set[Type] = set()
    for entry_point in module_entry_points:
        try:
            loaded_entry_point = entry_point.load()
            if inspect.isclass(loaded_entry_point):
                if not issubclass(loaded_entry_point, ModuleProtocol):
                    raise TypeError(f"Module entry point class '{loaded_entry_point.__name__}' from '{entry_point.module}' does not implement required static method 'def get_module_name() -> str'.")
                module_types.add(loaded_entry_point)
            elif inspect.ismodule(loaded_entry_point):
                # Get all classes defined in this module
                for _, obj in inspect.getmembers(loaded_entry_point, inspect.isclass):
                    if obj.__module__ == loaded_entry_point.__name__:
                        module_types.add(obj)
            elif inspect.isfunction(loaded_entry_point):
                raise TypeError("Module entry point cannot be a function.")
        except metadata.PackageNotFoundError:
            continue
    return module_types


class ModulesHandler:
    def __init__(self, io: IO) -> None:
        self._modules_instances: List[object] = []
        self._managed_protocols: dict[Type, List[object]] = {}
        self._io = io

    def instantiate_modules(self) -> None:
        module_types = _load_module_types()

        # Determine supported protocols including custom ones
        protocols: List[Type] = [
            GlobalSetupProtocol,
            CommandProtocol,
            TerminateProtocol,
            ErrorProtocol,
            SignalProtocol,
        ]
        for module_type in module_types:
            additional_protocols = self._resolve_custom_protocols(module_type)
            protocols.extend(additional_protocols)

        for module_type in module_types:
            # Get supported protocols for this module
            supported_protocols_by_module: List[Type] = [protocol for protocol in protocols if issubclass(module_type, protocol)]
            if not supported_protocols_by_module:
                # Module class does not support any known protocol
                continue
            # Instantiate the module
            sig = inspect.signature(module_type.__init__)
            module_instance = module_type(io=self._io) if 'io' in sig.parameters else module_type()
            self._modules_instances.append(module_instance)
            for protocol in supported_protocols_by_module:
                self._managed_protocols.setdefault(protocol, []).append(module_instance)

    def acquire_protocol_handlers[T:ModuleProtocol](self, protocol: Type[T]) -> List[T]:
        return self._managed_protocols.get(protocol, [])  # type: ignore

    def is_protocol_managed(self, protocol: Type) -> bool:
        return protocol in self._managed_protocols

    def _resolve_custom_protocols(self, module_cls: Type) -> List[Type]:
        if issubclass(module_cls, CustomProtocolsProtocol):
            return module_cls.declare_custom_protocols()
        return []

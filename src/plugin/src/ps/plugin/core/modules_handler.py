from typing import Iterable, List, Type
import inspect
from importlib import metadata

from poetry.console.application import Application
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
    module_types: list[tuple[str, Type]] = []
    for entry_point in module_entry_points:
        try:
            entry_spec = f"{entry_point.value}"
            loaded_entry_point = entry_point.load()
            if inspect.isclass(loaded_entry_point):
                if not issubclass(loaded_entry_point, ModuleProtocol):
                    raise TypeError(f"Module entry point class '{loaded_entry_point.__name__}' from '{entry_point.module}' does not implement required static method 'def get_module_name() -> str'.")
                module_types.append((entry_spec, loaded_entry_point))
            elif inspect.ismodule(loaded_entry_point):
                # Get all classes defined in this module
                for _, obj in inspect.getmembers(loaded_entry_point, inspect.isclass):
                    module_types.append((entry_spec, obj))
            elif inspect.isfunction(loaded_entry_point):
                raise TypeError("Module entry point cannot be a function.")
        except metadata.PackageNotFoundError:
            continue
    return module_types


def _resolve_custom_protocols(module_cls: Type) -> List[Type]:
    if not issubclass(module_cls, CustomProtocolsProtocol):
        return []
    custom_protocols = module_cls.declare_custom_protocols()
    for protocol in custom_protocols:
        if not hasattr(protocol, '__runtime_checkable__') or not protocol.__runtime_checkable__:
            raise TypeError(
                f"Custom protocol '{protocol.__name__}' declared by module '{module_cls.__name__}' "
                f"must be decorated with @runtime_checkable"
            )
    return custom_protocols


class ModulesHandler:
    def __init__(self, io: IO) -> None:
        self._modules_instances: List[object] = []
        self._managed_protocols: dict[Type, List[object]] = {}
        self._io = io

    def instantiate_modules(self, application: Application) -> None:
        module_entries = _load_module_class_types()
        module_types_list = [(entry_spec, module_type) for entry_spec, module_type in module_entries]
        if module_types_list:
            _log_verbose(self._io, f"Discovered {len(module_types_list)} module type(s)")
            for entry_spec, cls_name in module_types_list:
                _log_debug(self._io, f"  - <comment>{entry_spec}</comment> -> <fg=yellow>{cls_name.__name__}</>")
        else:
            _log_debug(self._io, "No module types discovered")
        # Determine supported protocols including custom ones
        protocols: List[Type] = [
            GlobalSetupProtocol,
            CommandProtocol,
            TerminateProtocol,
            ErrorProtocol,
            SignalProtocol,
        ]

        # Get unique module types for instantiation
        unique_module_types = {module_type for _, module_type in module_types_list}

        for module_type in unique_module_types:
            additional_protocols = _resolve_custom_protocols(module_type)
            if additional_protocols:
                _log_debug(self._io, f"Module <comment>{module_type.__name__}</comment> declares custom protocols: <fg=yellow>{[p.__name__ for p in additional_protocols]}</>")
            protocols.extend(additional_protocols)

        for module_type in unique_module_types:
            # Get supported protocols for this module
            supported_protocols_by_module: List[Type] = [protocol for protocol in protocols if issubclass(module_type, protocol)]
            if not supported_protocols_by_module:
                # Module class does not support any known protocol
                continue
            _log_debug(self._io, f"Module <comment>{module_type.__name__}</comment> supports {len(supported_protocols_by_module)} protocol(s):")
            for protocol in supported_protocols_by_module:
                _log_debug(self._io, f"  - <fg=yellow>{protocol.__name__}</>")
            # Instantiate the module
            module_instance = _instantiate_module(
                module_type,
                {
                    "io": self._io,
                    "application": application,
                })
            self._modules_instances.append(module_instance)
            for protocol in supported_protocols_by_module:
                self._managed_protocols.setdefault(protocol, []).append(module_instance)

    def acquire_protocol_handlers[T:ModuleProtocol](self, protocol: Type[T]) -> List[T]:
        return self._managed_protocols.get(protocol, [])  # type: ignore

    def is_protocol_managed(self, protocol: Type) -> bool:
        return protocol in self._managed_protocols

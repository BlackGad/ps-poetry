from typing import Iterable, List, Type
import inspect
from importlib import metadata

from cleo.io.io import IO

from ps.plugin.sdk import (
    ActivateProtocol,
    ListenerCommandProtocol,
    ListenerTerminateProtocol,
    ListenerErrorProtocol,
    ListenerSignalProtocol,
    DI,
    PluginSettings
)
from .logging import _log_debug, _get_module_verbal_name, _get_module_name


def _load_module_class_types() -> Iterable[tuple[str, Type]]:
    all_entries: list[tuple[str, Type]] = []

    for entry_point in metadata.entry_points(group="ps.module"):
        try:
            entry_spec = entry_point.value
            loaded_entry_point = entry_point.load()
            classes_to_add: list[Type] = []
            if inspect.isclass(loaded_entry_point):
                classes_to_add.append(loaded_entry_point)
            elif inspect.ismodule(loaded_entry_point):
                classes_to_add.extend(
                    obj for _, obj in inspect.getmembers(loaded_entry_point, inspect.isclass)
                    if obj.__module__.startswith(loaded_entry_point.__name__)
                )
            elif inspect.isfunction(loaded_entry_point):
                raise TypeError("Module entry point cannot be a function.")
            all_entries.extend((entry_spec, module_type) for module_type in classes_to_add)
        except metadata.PackageNotFoundError:
            continue

    # Keep only the longest entry_spec for each module_type
    type_to_entry: dict[Type, str] = {}
    for entry_spec, module_type in all_entries:
        existing_spec = type_to_entry.get(module_type)
        if existing_spec is None or len(entry_spec) > len(existing_spec):
            type_to_entry[module_type] = entry_spec

    return [(entry_spec, module_type) for module_type, entry_spec in type_to_entry.items()]


class ModulesHandler:
    def __init__(self, di: DI) -> None:
        self._modules_instances: List[object] = []
        self._managed_protocols: dict[Type, List[object]] = {}
        self._di = di

    def instantiate_modules(self) -> None:
        io = self._di.resolve(IO)
        assert io is not None
        plugin_settings = self._di.resolve(PluginSettings)
        assert plugin_settings is not None
        specified_modules = plugin_settings.modules
        module_entries = _load_module_class_types()
        all_module_types_list = [(entry_spec, module_type) for entry_spec, module_type in module_entries]
        name_to_entry: dict[str, tuple[str, Type]] = {
            _get_module_name(module_type): (entry_spec, module_type)
            for entry_spec, module_type in all_module_types_list
        }

        if specified_modules is not None:
            # Ordered selection: keep only specified, in user-defined order
            module_types_list = [
                name_to_entry[name]
                for name in specified_modules
                if name in name_to_entry
            ]
            selected_names = {name for name in specified_modules if name in name_to_entry}
        else:
            module_types_list = all_module_types_list
            selected_names = set(name_to_entry.keys())

        available_not_selected = [
            (entry_spec, module_type)
            for entry_spec, module_type in all_module_types_list
            if _get_module_name(module_type) not in selected_names
        ]

        if io.is_verbose():
            io.write_line("<fg=magenta>Selected modules:</>")
            for idx, (entry_spec, module_type) in enumerate(module_types_list, start=1):
                suffix = f" <fg=dark_gray>[{entry_spec}]</>" if io.is_debug() else ""
                io.write_line(f"  {idx}. <fg=cyan>{_get_module_name(module_type)}</>{suffix}")

        if io.is_debug() and available_not_selected:
            io.write_line("\n<fg=magenta>Available but not selected:</>")
            for entry_spec, module_type in available_not_selected:
                suffix = f" <fg=dark_gray>[{entry_spec}]</>" if io.is_debug() else ""
                io.write_line(f"  - <fg=dark_gray>{_get_module_name(module_type)}</>{suffix}")

        protocols: List[Type] = [
            ActivateProtocol,
            ListenerCommandProtocol,
            ListenerTerminateProtocol,
            ListenerErrorProtocol,
            ListenerSignalProtocol,
        ]

        unique_module_types = list(dict.fromkeys(module_type for _, module_type in module_types_list))

        for module_type in unique_module_types:
            # Get supported protocols for this module
            supported_protocols_by_module: List[Type] = [protocol for protocol in protocols if issubclass(module_type, protocol)]
            if not supported_protocols_by_module:
                # Module class does not support any known protocol
                continue
            _log_debug(io, f"Module <comment>{_get_module_verbal_name(module_type)}</comment> supports {len(supported_protocols_by_module)} protocol(s):")
            for protocol in supported_protocols_by_module:
                _log_debug(io, f"  - <fg=yellow>{protocol.__name__}</>")
            # Instantiate the module
            module_instance = self._di.spawn(module_type)
            self._modules_instances.append(module_instance)
            for protocol in supported_protocols_by_module:
                self._managed_protocols.setdefault(protocol, []).append(module_instance)

    def acquire_protocol_handlers[T](self, protocol: Type[T]) -> List[T]:
        return self._managed_protocols.get(protocol, [])  # type: ignore

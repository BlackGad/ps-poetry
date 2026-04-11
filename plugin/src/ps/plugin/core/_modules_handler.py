import inspect
import re
import traceback
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any, Callable, Optional

from cleo.io.io import IO

from ps.di import DI
from ps.plugin.sdk.logging import log_debug, log_verbose
from ps.plugin.sdk.settings import PluginSettings

_HANDLER_PATTERN = re.compile(r"^poetry_(activate|command|error|terminate|signal)(_\w+)?$")
_EVENT_TYPES = ("activate", "command", "error", "terminate", "signal")


@dataclass
class _ModuleInfo:
    name: str
    handlers: dict[str, Callable] = field(default_factory=dict)
    distribution: Optional[str] = None
    instance: Optional[object] = None
    path: Optional[str] = None


def _get_module_path(obj: Any) -> Optional[str]:
    try:
        return inspect.getfile(obj)
    except (TypeError, OSError):
        return None


def _get_distribution(entry_point: metadata.EntryPoint) -> Optional[str]:
    try:
        return entry_point.dist.name if entry_point.dist else None
    except Exception:
        return None


def _get_class_name(cls: type) -> str:
    name_attr = getattr(cls, "name", None)
    return name_attr if isinstance(name_attr, str) else cls.__name__


def _is_static_or_classmethod(cls: type, name: str) -> bool:
    for klass in cls.__mro__:
        if name in klass.__dict__:
            val = klass.__dict__[name]
            return isinstance(val, (staticmethod, classmethod))
    return False


def _scan_class(cls: type, distribution: Optional[str]) -> list[_ModuleInfo]:
    instance_handlers: dict[str, Callable] = {}
    static_handlers: dict[str, tuple[str, Callable]] = {}

    for name in dir(cls):
        match = _HANDLER_PATTERN.match(name)
        if not match:
            continue
        event_type = match.group(1)
        suffix = (match.group(2) or "")[1:]  # strip leading _

        if _is_static_or_classmethod(cls, name):
            if not suffix:
                continue  # static/class methods MUST have suffix
            fn = getattr(cls, name)
            static_handlers[name] = (suffix, fn)
        else:
            instance_handlers[event_type] = getattr(cls, name)

    modules: list[_ModuleInfo] = []

    cls_path = _get_module_path(cls)

    if instance_handlers:
        modules.append(_ModuleInfo(
            name=_get_class_name(cls),
            handlers=instance_handlers,
            distribution=distribution,
            path=cls_path,
        ))

    # Group static methods by suffix
    suffix_groups: dict[str, dict[str, Callable]] = {}
    for name, (suffix, fn) in static_handlers.items():
        match = _HANDLER_PATTERN.match(name)
        if match:
            event_type = match.group(1)
            suffix_groups.setdefault(suffix, {})[event_type] = fn

    for suffix, handlers in suffix_groups.items():
        modules.append(_ModuleInfo(
            name=suffix,
            handlers=handlers,
            distribution=distribution,
            path=cls_path,
        ))

    return modules


def _scan_function(fn: Callable, distribution: Optional[str]) -> Optional[_ModuleInfo]:
    name = getattr(fn, "__name__", "")
    match = _HANDLER_PATTERN.match(name)
    if not match:
        return None
    event_type = match.group(1)
    suffix = (match.group(2) or "")[1:]
    if not suffix:
        return None  # global functions MUST have suffix
    return _ModuleInfo(name=suffix, handlers={event_type: fn}, distribution=distribution, path=_get_module_path(fn))


def _load_module_infos(io: IO) -> list[_ModuleInfo]:
    all_modules: list[_ModuleInfo] = []

    for entry_point in metadata.entry_points(group="ps.module"):
        ep_name = f"{entry_point.group}:{entry_point.name}"
        try:
            loaded = entry_point.load()
            dist = _get_distribution(entry_point)
        except Exception as e:
            log_verbose(io, f"  <fg=yellow>Warning: failed to load entry point '{ep_name}': {e}</>")
            log_debug(io, f"  <fg=dark_gray>{traceback.format_exc().strip()}</>")
            continue

        if inspect.isclass(loaded):
            all_modules.extend(_scan_class(loaded, dist))
        elif inspect.ismodule(loaded):
            for _, obj in inspect.getmembers(loaded):
                if inspect.isclass(obj) and obj.__module__.startswith(loaded.__name__):
                    all_modules.extend(_scan_class(obj, dist))
                elif inspect.isfunction(obj) and obj.__module__ == loaded.__name__:
                    info = _scan_function(obj, dist)
                    if info:
                        all_modules.append(info)
        elif inspect.isfunction(loaded):
            info = _scan_function(loaded, dist)
            if info:
                all_modules.append(info)
        else:
            log_verbose(io, f"  <fg=yellow>Warning: entry point '{ep_name}' loaded unsupported type {type(loaded).__name__}, skipping.</>")

    return all_modules


def _detect_collisions(modules: list[_ModuleInfo], io: IO) -> list[_ModuleInfo]:
    name_groups: dict[str, list[_ModuleInfo]] = {}
    for mod in modules:
        name_groups.setdefault(mod.name, []).append(mod)

    result: list[_ModuleInfo] = []
    for name, group in name_groups.items():
        if len(group) == 1:
            result.append(group[0])
            continue

        paths = {m.path for m in group}
        if len(paths) == 1 and None not in paths:
            log_debug(io, f"<fg=dark_gray>Module '<fg=cyan>{name}</>' discovered via multiple entry points, using single instance</>")
            result.append(group[0])
        else:
            dist_list = ", ".join(
                f"<fg=yellow>{m.distribution or 'unknown'}</>" for m in group
            )
            log_verbose(
                io,
                f"  <fg=yellow>Warning: module name collision: '<fg=cyan>{name}</>' found in [{dist_list}]. None will be loaded.</>",
            )
            if io.is_debug():
                for m in group:
                    path_hint = f" — {m.path}" if m.path else ""
                    io.write_line(f"    <fg=dark_gray>  {m.distribution or 'unknown'}{path_hint}</>")
    return result


class _ModulesHandler:
    def __init__(self, di: DI, io: IO, plugin_settings: PluginSettings) -> None:
        self._di = di
        self._io = io
        self._plugin_settings = plugin_settings
        self._modules: list[_ModuleInfo] = []
        self._disabled: set[str] = set()

    def discover_and_instantiate(self) -> None:
        io = self._io
        all_modules = _load_module_infos(io)
        modules = _detect_collisions(all_modules, io)

        specified = self._plugin_settings.modules
        if specified is not None:
            name_map = {m.name: m for m in modules}
            modules = [name_map[n] for n in specified if n in name_map]
            selected_names = {m.name for m in modules}
        else:
            modules = []
            selected_names = set()

        if io.is_verbose():
            available_not_selected = [m for m in all_modules if m.name not in selected_names]

            io.write_line("<fg=magenta>Selected modules:</>")
            for idx, mod in enumerate(modules, start=1):
                dist_hint = f" <fg=dark_gray>[{mod.distribution}]</>" if mod.distribution else ""
                io.write_line(f"  {idx}. <fg=cyan>{mod.name}</>{dist_hint}")
                if io.is_debug() and mod.path:
                    io.write_line(f"       <fg=dark_gray>{mod.path}</>")

            if available_not_selected:
                io.write_line("<fg=magenta>Discovered but not selected:</>")
                for mod in available_not_selected:
                    dist_hint = f" <fg=dark_gray>[{mod.distribution}]</>" if mod.distribution else ""
                    io.write_line(f"  - <fg=dark_gray>{mod.name}</>{dist_hint}")
                    if io.is_debug() and mod.path:
                        io.write_line(f"       <fg=dark_gray>{mod.path}</>")

        # Instantiate class-based modules
        for mod in modules:
            handlers = mod.handlers
            # Check if any handler is an unbound method (needs instance)
            needs_instance = any(
                _is_unbound_method(fn) for fn in handlers.values()
            )
            if needs_instance:
                # Find the class from first unbound method
                cls = _get_defining_class(next(iter(handlers.values())))
                if cls:
                    instance = self._di.spawn(cls)
                    mod.instance = instance
                    # Bind methods to instance
                    mod.handlers = {
                        event_type: getattr(instance, _event_to_method_name(event_type, mod.name, cls))
                        for event_type, fn in handlers.items()
                    }
                    log_debug(io, f"<fg=dark_gray>Instantiated module <comment>{mod.name}</comment> ({cls.__module__}.{cls.__name__})</>")

            event_types = ", ".join(sorted(mod.handlers.keys()))
            log_debug(io, f"<fg=dark_gray>Module <comment>{mod.name}</comment> handles: {event_types}</>")

        self._modules = modules

    def activate(self) -> None:
        io = self._io
        activate_modules = [m for m in self._modules if "activate" in m.handlers]
        log_verbose(io, f"<info>Activating {len(activate_modules)} module(s)</info>")

        for mod in activate_modules:
            fn = mod.handlers["activate"]
            log_debug(io, f"<fg=dark_gray>Executing activate for module <comment>{mod.name}</comment></>")
            try:
                result = self._di.satisfy(fn)()
                if result is False:
                    self._disabled.add(mod.name)
                    log_debug(io, f"<fg=dark_gray>Module <comment>{mod.name}</comment> disabled itself during activation</>")
            except Exception as e:
                io.write_error_line(f"<error>Error during activation of module {mod.name}: {e}</error>")
                raise

    def get_event_handlers(self, event_type: str) -> list[Callable[..., Any]]:
        return [
            mod.handlers[event_type]
            for mod in self._modules
            if event_type in mod.handlers and mod.name not in self._disabled
        ]

    def get_module_names(self) -> list[str]:
        return [m.name for m in self._modules if m.name not in self._disabled]


def _is_unbound_method(fn: Callable) -> bool:
    return inspect.isfunction(fn) and "." in getattr(fn, "__qualname__", "")


def _get_defining_class(fn: Callable) -> Optional[type]:
    qualname = getattr(fn, "__qualname__", "")
    parts = qualname.rsplit(".", 1)
    if len(parts) < 2:
        return None
    module = inspect.getmodule(fn)
    if module is None:
        return None
    return getattr(module, parts[0], None)


def _event_to_method_name(event_type: str, module_name: str, cls: type) -> str:
    # Try without suffix first (instance methods can omit suffix)
    base = f"poetry_{event_type}"
    if hasattr(cls, base):
        return base
    # Try with module name as suffix
    return f"poetry_{event_type}_{module_name}"

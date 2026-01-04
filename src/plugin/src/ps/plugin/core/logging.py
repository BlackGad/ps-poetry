from typing import Type, Union
from cleo.io.io import IO


def _get_module_verbal_name(obj: Union[Type, object], include_type: bool = False) -> str:
    cls = obj if isinstance(obj, type) else type(obj)
    cls_name = f"<fg=dark_gray>{cls.__module__}.{cls.__name__}</>"
    name_attr = getattr(cls, "name", None)

    if isinstance(name_attr, str):
        return f"<fg=light_green>{name_attr}</> ({cls_name})" if include_type else name_attr

    return cls_name


def _get_module_name(obj: Union[Type, object]) -> str:
    cls = obj if isinstance(obj, type) else type(obj)
    cls_name = f"{cls.__module__}.{cls.__name__}"
    name_attr = getattr(cls, "name", None)

    if isinstance(name_attr, str):
        return name_attr

    return cls_name


def _log_verbose(io: IO, message: str) -> None:
    if io.is_verbose():
        io.write_line(f"<fg=magenta>PS:</> {message}")


def _log_debug(io: IO, message: str) -> None:
    if io.is_debug():
        io.write_line(f"<fg=dark_gray>PS:</> {message}")

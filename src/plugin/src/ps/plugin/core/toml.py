from typing import Any, Optional


def get_declaration[T](data: dict, path: str, default: Optional[Any] = None) -> Any:
    for key in path.split("."):
        if not isinstance(data, dict):
            return default
        item = data.get(key)
        if not isinstance(item, dict):
            return default
        data = item
    return data if isinstance(data, dict) else default

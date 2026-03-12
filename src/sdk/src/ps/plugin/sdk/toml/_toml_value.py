from typing import Any, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, computed_field
from tomlkit import TOMLDocument
from tomlkit.items import AoT, Table


Token = Tuple[str, Any]  # ("key", str) or ("index", int)


def _parse_jsonpath(path: str) -> List[Token]:
    if not path or path[0] != "$":
        raise ValueError('JSONPath must start with "$"')

    i, tokens = 1, []

    while i < len(path):
        if path[i] == ".":
            i += 1
            if i >= len(path) or not (path[i].isalpha() or path[i] == "_"):
                raise ValueError(f"Invalid key start at position {i} in JSONPath: {path!r}")
            start = i
            while i < len(path) and (path[i].isalnum() or path[i] in "_-"):
                i += 1
            tokens.append(("key", path[start:i]))
        elif path[i] == "[":
            i += 1
            if i >= len(path) or not path[i].isdigit():
                raise ValueError(f"Expected digit after '[' at position {i} in JSONPath: {path!r}")
            start = i
            while i < len(path) and path[i].isdigit():
                i += 1
            if i >= len(path) or path[i] != "]":
                raise ValueError(f"Expected ']' after index at position {i} in JSONPath: {path!r}")
            tokens.append(("index", int(path[start:i])))
            i += 1
        else:
            raise ValueError(f"Unexpected character {path[i]!r} at position {i} in JSONPath: {path!r}")

    return tokens


def _get_by_jsonpath(document: Any, jsonpath: str) -> Any:
    cur = document
    for _, val in _parse_jsonpath(jsonpath):
        cur = cur[val]
    return cur


def _set_by_jsonpath(document: Any, jsonpath: str, new_value: Any) -> None:
    tokens = _parse_jsonpath(jsonpath)
    if not tokens:
        raise ValueError("Cannot set root '$'")

    cur = document
    for _, val in tokens[:-1]:
        cur = cur[val]

    cur[tokens[-1][1]] = new_value


def _find_first_existing_jsonpath(document: Any, dotted: str) -> Optional[str]:
    def rec(node: Any, parts: List[str], path: str) -> Optional[str]:
        if not parts:
            return path
        head, *tail = parts
        if isinstance(node, (TOMLDocument, Table, dict)):
            return rec(node[head], tail, f"{path}.{head}") if head in node else None
        if isinstance(node, (AoT, list)):
            for i, item in enumerate(node):
                if result := rec(item, parts, f"{path}[{i}]"):
                    return result
        return None

    return rec(document, dotted.split("."), "$")


class TomlValue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    document: TOMLDocument = Field(exclude=True)
    jsonpath: Optional[str] = None

    @property
    def exists(self) -> bool:
        if not self.jsonpath:
            return False
        try:
            _get_by_jsonpath(self.document, self.jsonpath)
            return True
        except (KeyError, IndexError, Exception):
            return False

    @computed_field
    @property
    def value(self) -> Optional[Any]:
        if not self.jsonpath:
            return None
        try:
            return _get_by_jsonpath(self.document, self.jsonpath)
        except (KeyError, IndexError, Exception):
            return None

    def set(self, new_value: Any) -> None:
        if not self.jsonpath:
            raise ValueError("Path not found")
        _set_by_jsonpath(self.document, self.jsonpath, new_value)

    @staticmethod
    def locate(document: TOMLDocument, dotted_candidates: List[str]) -> 'TomlValue':
        for dotted in dotted_candidates:
            jp = _find_first_existing_jsonpath(document, dotted)
            if jp:
                return TomlValue(document=document, jsonpath=jp)
        # If no existing path found, use first candidate as fallback
        if dotted_candidates:
            fallback_path = f"$.{dotted_candidates[0]}"
            return TomlValue(document=document, jsonpath=fallback_path)
        return TomlValue(document=document, jsonpath=None)

from typing import Optional

from ps.version import VersionPicker


class SimpleObject:
    def __init__(self):
        self.value = "simple"


class NestedObject:
    def __init__(self):
        self.level1 = SimpleObject()
        self.level1.level2 = SimpleObject()  # type: ignore[attr-defined]
        self.level1.level2.level3 = "deep_value"  # type: ignore[attr-defined]


def test_nested_property_access():
    instance = NestedObject()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:level1:level2:level3}") == "deep_value"


def test_nested_property_partial_resolution():
    instance = NestedObject()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:level1:missing}") == "{config:level1:missing}"


def test_nested_property_first_level_missing():
    instance = SimpleObject()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:missing:sub}") == "{config:missing:sub}"


class GetAttrOverride:
    def __getattr__(self, name: str) -> str:
        if name == "dynamic":
            return "dynamic_value"
        if name == "number":
            return "42"
        raise AttributeError(f"No attribute {name}")


def test_getattr_override_success():
    instance = GetAttrOverride()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:dynamic}") == "dynamic_value"
    assert picker.materialize("{config:number}") == "42"


def test_getattr_override_missing():
    instance = GetAttrOverride()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:missing}") == "{config:missing}"


class GetAttrWithNested:
    def __init__(self):
        self.nested = SimpleObject()
        self.nested.value = "nested_value"  # type: ignore[attr-defined]

    def __getattr__(self, name: str) -> str:
        if name == "dynamic":
            return "from_getattr"
        raise AttributeError(f"No attribute {name}")


def test_getattr_with_real_nested_property():
    instance = GetAttrWithNested()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:nested:value}") == "nested_value"
    assert picker.materialize("{config:dynamic}") == "from_getattr"


class ConfirmWithNested:
    def __init__(self):
        self.allowed = SimpleObject()
        self.allowed.sub = "allowed_value"  # type: ignore[attr-defined]
        self.denied = SimpleObject()
        self.denied.sub = "denied_value"  # type: ignore[attr-defined]

    def confirm_resolve(self, args: list[str], resolved: str) -> bool:
        return args[0] == "allowed"


def test_confirm_with_nested_allowed():
    instance = ConfirmWithNested()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:allowed:sub}") == "allowed_value"


def test_confirm_with_nested_denied():
    instance = ConfirmWithNested()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:denied:sub}") == "{config:denied:sub}"


class CallableWithGetAttr:
    def __getattr__(self, name: str) -> Optional[str]:
        if name == "attr":
            return None
        raise AttributeError(f"No attribute {name}")

    def __call__(self, args: list[str]) -> Optional[str]:
        if args and args[0] == "callable":
            return "from_call"
        return None


def test_getattr_returns_none_fallback_to_call():
    instance = CallableWithGetAttr()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:attr}") == "{config:attr}"
    assert picker.materialize("{config:callable}") == "from_call"


class ChainedNested:
    def __init__(self):
        self.a = SimpleObject()
        self.a.b = SimpleObject()  # type: ignore[attr-defined]
        self.a.b.c = SimpleObject()  # type: ignore[attr-defined]
        self.a.b.c.d = "final"  # type: ignore[attr-defined]


def test_deep_nested_chain():
    instance = ChainedNested()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:a:b:c:d}") == "final"


def test_deep_nested_chain_break_middle():
    instance = ChainedNested()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:a:b:x:d}") == "{config:a:b:x:d}"


class MixedTypeNested:
    def __init__(self):
        self.num = 42
        self.obj = SimpleObject()
        self.obj.num = 123  # type: ignore[attr-defined]


def test_nested_with_numeric_value():
    instance = MixedTypeNested()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:num}") == "42"
    assert picker.materialize("{config:obj:num}") == "123"


class GetAttrReturnsObject:
    class Inner:
        def __init__(self):
            self.value = "inner_value"

    def __getattr__(self, name: str):
        if name == "inner":
            return self.Inner()
        raise AttributeError(f"No attribute {name}")


def test_getattr_returns_object_with_nested():
    instance = GetAttrReturnsObject()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:inner:value}") == "inner_value"


class ConfirmWithGetAttr:
    def __getattr__(self, name: str) -> str:
        if name == "dynamic":
            return "dynamic_value"
        raise AttributeError(f"No attribute {name}")

    def confirm_resolve(self, args: list[str], resolved: str) -> bool:
        return resolved == "dynamic_value"


def test_confirm_with_getattr_allowed():
    instance = ConfirmWithGetAttr()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:dynamic}") == "dynamic_value"


class ConfirmWithGetAttrDenied:
    def __getattr__(self, name: str) -> str:
        return "any_value"

    def confirm_resolve(self, args: list[str], resolved: str) -> bool:
        return False

    def __call__(self, args: list[str]) -> Optional[str]:
        return "from_callable"


def test_confirm_denied_fallback_to_call():
    instance = ConfirmWithGetAttrDenied()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:anything}") == "from_callable"


class NestedNoneValue:
    def __init__(self):
        self.obj = SimpleObject()
        self.obj.none_value = None  # type: ignore[attr-defined]


def test_nested_none_stops_resolution():
    instance = NestedNoneValue()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:obj:none_value:further}") == "{config:obj:none_value:further}"

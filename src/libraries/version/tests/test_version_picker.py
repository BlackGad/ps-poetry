from typing import Optional

from ps.version import VersionPicker


class SimpleInstance:
    def __init__(self):
        self.version = "1.2.3"
        self.build = 456


def test_instance_resolver_field_access():
    instance = SimpleInstance()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:version}") == "1.2.3"
    assert picker.materialize("{config:build}") == "456"


def test_instance_resolver_missing_field():
    instance = SimpleInstance()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:missing}") == "{config:missing}"


class InstanceWithConfirm:
    def __init__(self):
        self.allowed = "yes"
        self.denied = "no"

    def confirm_resolve(self, args: list[str], resolved: str) -> bool:
        return args[0] == "allowed"


def test_instance_resolver_with_confirm_allowed():
    instance = InstanceWithConfirm()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:allowed}") == "yes"


def test_instance_resolver_with_confirm_denied():
    instance = InstanceWithConfirm()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:denied}") == "{config:denied}"


class CallableInstance:
    def __init__(self):
        self.value = "field"

    def __call__(self, args: list[str]) -> Optional[str]:
        if args and args[0] == "custom":
            return "callable"
        return None


def test_instance_resolver_callable_fallback():
    instance = CallableInstance()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:value}") == "field"
    assert picker.materialize("{config:custom}") == "callable"


def test_instance_resolver_callable_when_field_missing():
    instance = CallableInstance()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:missing}") == "{config:missing}"
    assert picker.materialize("{config:custom}") == "callable"


class InstanceWithConfirmAndCallable:
    def __init__(self):
        self.rejected = "rejected_value"

    def confirm_resolve(self, args: list[str], resolved: str) -> bool:
        return False

    def __call__(self, args: list[str]) -> Optional[str]:
        return "fallback_from_call"


def test_instance_resolver_confirm_reject_then_call():
    instance = InstanceWithConfirmAndCallable()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:rejected}") == "fallback_from_call"


def test_instance_resolver_empty_args():
    instance = SimpleInstance()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config}") == "{config}"


class InstanceOnlyCallable:
    def __call__(self, args: list[str]) -> Optional[str]:
        return "only_callable"


def test_instance_resolver_only_callable():
    instance = InstanceOnlyCallable()
    picker = VersionPicker([("config", instance)])
    assert picker.materialize("{config:anything}") == "only_callable"


def test_instance_resolver_with_function():
    def my_resolver(_args: list[str]) -> Optional[str]:
        return "from_function"

    instance = SimpleInstance()
    picker = VersionPicker([("func", my_resolver), ("inst", instance)])
    assert picker.materialize("{func:test}") == "from_function"
    assert picker.materialize("{inst:version}") == "1.2.3"

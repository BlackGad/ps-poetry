import pytest
from typing import List, Optional

from ps.di import DI, REQUIRED

from .conftest import Counter, Service


def test_satisfy_returns_callable():
    di = DI()

    def fn(name: str) -> str:
        return name

    di.register(Service).factory(lambda: Service("s"))
    wrapper = di.satisfy(fn, name="hello")

    assert callable(wrapper)


def test_satisfy_calls_function_with_explicit_kwargs():
    di = DI()

    def greet(name: str) -> str:
        return f"hello {name}"

    wrapper = di.satisfy(greet, name="world")
    result = wrapper()

    assert result == "hello world"


def test_satisfy_resolves_di_dependency():
    di = DI()
    di.register(Service).factory(lambda: Service("resolved"))

    def fn(service: Service) -> str:
        return service.name

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert result == "resolved"


def test_satisfy_explicit_param_overrides_di():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))
    manual_service = Service("manual")

    def fn(service: Service) -> str:
        return service.name

    wrapper = di.satisfy(fn, service=manual_service)
    result = wrapper()

    assert result == "manual"


def test_satisfy_uses_default_when_not_resolved():
    di = DI()

    def fn(value: str = "default") -> str:
        return value

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert result == "default"


def test_satisfy_optional_not_registered_returns_none():
    di = DI()

    def fn(service: Optional[Service] = None) -> Optional[Service]:
        return service

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert result is None


def test_satisfy_optional_without_default_returns_none():
    di = DI()

    def fn(service: Optional[Service]) -> Optional[Service]:
        return service

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert result is None


def test_satisfy_resolves_optional_when_registered():
    di = DI()
    di.register(Service).factory(lambda: Service("found"))

    def fn(service: Optional[Service] = None) -> Optional[Service]:
        return service

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert result is not None
    assert result.name == "found"


def test_satisfy_raises_for_unresolved_required_param():
    di = DI()

    def fn(service: Service) -> str:
        return service.name

    with pytest.raises(ValueError) as exc_info:
        di.satisfy(fn)

    assert "Cannot resolve required dependency" in str(exc_info.value)
    assert "service" in str(exc_info.value)


def test_satisfy_resolves_at_satisfy_time_not_call_time():
    di = DI()
    di.register(Service).factory(lambda: Service("original"))

    def fn(service: Service) -> str:
        return service.name

    wrapper = di.satisfy(fn)

    di.register(Service).factory(lambda: Service("updated"))
    result = wrapper()

    assert result == "original"


def test_satisfy_resolves_list_dependency():
    di = DI()
    di.register(Service).factory(lambda: Service("first"))
    di.register(Service).factory(lambda: Service("second"))

    def fn(services: List[Service]) -> List[Service]:
        return services

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert len(result) == 2


def test_satisfy_injects_di_instance():
    di = DI()

    def fn(di_instance: DI) -> DI:
        return di_instance

    wrapper = di.satisfy(fn)
    result = wrapper()

    assert result is di


def test_satisfy_mixed_explicit_and_resolved():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))
    di.register(Counter).factory(lambda: Counter())

    def fn(name: str, service: Service, counter: Counter) -> str:
        return f"{name}:{service.name}:{counter.value}"

    wrapper = di.satisfy(fn, name="test")
    result = wrapper()

    assert result == "test:from-di:0"


def test_satisfy_wrapper_can_override_resolved_param():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))

    def fn(service: Service) -> str:
        return service.name

    wrapper = di.satisfy(fn)
    manual = Service("override")
    result = wrapper(service=manual)

    assert result == "override"


def test_satisfy_wrapper_can_override_explicit_param():
    di = DI()

    def fn(name: str) -> str:
        return name

    wrapper = di.satisfy(fn, name="original")
    result = wrapper(name="overridden")

    assert result == "overridden"


def test_satisfy_required_skips_di_resolution():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))

    def fn(service: Service) -> str:
        return service.name

    manual = Service("manual")
    wrapper = di.satisfy(fn, service=REQUIRED)
    result = wrapper(service=manual)

    assert result == "manual"


def test_satisfy_required_must_be_provided_at_call_time():
    di = DI()

    def fn(name: str) -> str:
        return name

    wrapper = di.satisfy(fn, name=REQUIRED)

    with pytest.raises(TypeError):
        wrapper()  # type: ignore[call-arg]


def test_satisfy_required_not_resolved_even_when_di_has_it():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))

    def fn(service: Service) -> str:
        return service.name

    manual = Service("caller-provided")
    wrapper = di.satisfy(fn, service=REQUIRED)
    result = wrapper(service=manual)

    assert result == "caller-provided"


def test_satisfy_required_repr():
    assert repr(REQUIRED) == "REQUIRED"


def test_satisfy_mixed_required_resolved_and_override():
    di = DI()
    di.register(Counter).factory(lambda: Counter())

    def fn(name: str, label: str, counter: Counter) -> str:
        return f"{name}:{label}:{counter.value}"

    wrapper = di.satisfy(fn, name=REQUIRED, label="fixed")
    result = wrapper(name="dynamic")

    assert result == "dynamic:fixed:0"

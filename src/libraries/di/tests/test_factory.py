import pytest
from typing import List, Optional

from ps.di import DI

from .conftest import Counter, DependentService, Service


def test_factory_auto_resolves_typed_dependency():
    di = DI()
    di.register(Service).factory(lambda: Service("injected"))
    di.register(DependentService).factory(DependentService)

    result = di.resolve(DependentService)

    assert result is not None
    assert result.service.name == "injected"


def test_factory_explicit_positional_arg_overrides_di_resolution():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))
    manual = Service("manual")
    di.register(DependentService).factory(DependentService, manual)

    result = di.resolve(DependentService)

    assert result is not None
    assert result.service.name == "manual"


def test_factory_explicit_kwarg_overrides_di_resolution():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))
    manual = Service("manual")
    di.register(DependentService).factory(DependentService, service=manual)

    result = di.resolve(DependentService)

    assert result is not None
    assert result.service.name == "manual"


def test_factory_optional_param_defaults_to_none_when_not_registered():
    di = DI()
    di.register(Service).factory(lambda: Service("s"))

    class ServiceWithOptionalCounter:
        def __init__(self, service: Service, counter: Optional[Counter] = None) -> None:
            self.service = service
            self.counter = counter

    di.register(ServiceWithOptionalCounter).factory(ServiceWithOptionalCounter)

    result = di.resolve(ServiceWithOptionalCounter)

    assert result is not None
    assert result.counter is None


def test_factory_optional_param_resolved_when_registered():
    di = DI()
    di.register(Service).factory(lambda: Service("s"))
    di.register(Counter).factory(Counter)

    class ServiceWithOptionalCounter:
        def __init__(self, service: Service, counter: Optional[Counter] = None) -> None:
            self.service = service
            self.counter = counter

    di.register(ServiceWithOptionalCounter).factory(ServiceWithOptionalCounter)

    result = di.resolve(ServiceWithOptionalCounter)

    assert result is not None
    assert result.counter is not None
    assert result.counter.value == 0


def test_factory_resolves_list_param():
    di = DI()
    di.register(Service).factory(lambda: Service("first"))
    di.register(Service).factory(lambda: Service("second"))

    class MultiConsumer:
        def __init__(self, services: List[Service]) -> None:
            self.services = services

    di.register(MultiConsumer).factory(MultiConsumer)

    result = di.resolve(MultiConsumer)

    assert result is not None
    assert len(result.services) == 2


def test_factory_injects_di_itself():
    di = DI()

    class ServiceWithDI:
        def __init__(self, container: DI) -> None:
            self.container = container

    di.register(ServiceWithDI).factory(ServiceWithDI)

    result = di.resolve(ServiceWithDI)

    assert result is not None
    assert result.container is di


def test_factory_raises_when_required_param_cannot_be_resolved():
    di = DI()

    with pytest.raises(ValueError) as exc_info:
        di.register(DependentService).factory(DependentService)

    assert "Cannot resolve required dependency" in str(exc_info.value)


def test_factory_captures_dependencies_at_registration_time():
    di = DI()
    di.register(Service).factory(lambda: Service("original"))

    di.register(DependentService).factory(DependentService)

    di.register(Service).factory(lambda: Service("updated"))

    result = di.resolve(DependentService)

    assert result is not None
    assert result.service.name == "original"


def test_factory_mixed_explicit_and_di_resolved():
    di = DI()
    di.register(Counter).factory(Counter)
    di.register(Service).factory(lambda: Service("s"))

    class Named:
        def __init__(self, name: str, service: Service, counter: Counter) -> None:
            self.name = name
            self.service = service
            self.counter = counter

    di.register(Named).factory(Named, "test-name")

    result = di.resolve(Named)

    assert result is not None
    assert result.name == "test-name"
    assert result.service.name == "s"
    assert result.counter.value == 0

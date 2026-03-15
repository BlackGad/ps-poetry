import pytest
from typing import List, Optional

from ps.di import DI

from .conftest import ComplexService, Counter, DependentService, Service


def test_spawn_with_args_and_kwargs():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))

    instance = di.spawn(Service, "manual-name")

    assert instance.name == "manual-name"


def test_spawn_with_kwargs():
    di = DI()
    di.register(Service).factory(lambda: Service("from-di"))

    instance = di.spawn(Service, name="manual-name")

    assert instance.name == "manual-name"


def test_spawn_resolves_simple_dependency():
    di = DI()
    di.register(Service).factory(lambda: Service("resolved-service"))

    instance = di.spawn(DependentService)

    assert instance.service is not None
    assert instance.service.name == "resolved-service"


def test_spawn_resolves_optional_dependency():
    di = DI()
    di.register(Counter).factory(lambda: Counter())

    class ServiceWithOptional:
        def __init__(self, counter: Optional[Counter] = None) -> None:
            self.counter = counter

    instance = di.spawn(ServiceWithOptional)

    assert instance.counter is not None
    assert instance.counter.value == 0


def test_spawn_optional_dependency_not_registered():
    di = DI()

    class ServiceWithOptional:
        def __init__(self, counter: Optional[Counter] = None) -> None:
            self.counter = counter

    instance = di.spawn(ServiceWithOptional)

    assert instance.counter is None


def test_spawn_resolves_list_dependency():
    di = DI()
    di.register(Service).factory(lambda: Service("service-1"))
    di.register(Service).factory(lambda: Service("service-2"))

    class ServiceWithList:
        def __init__(self, services: List[Service]) -> None:
            self.services = services

    instance = di.spawn(ServiceWithList)

    assert len(instance.services) == 2
    assert instance.services[0].name == "service-2"
    assert instance.services[1].name == "service-1"


def test_spawn_uses_default_value_when_dependency_not_resolved():
    di = DI()

    class ServiceWithDefault:
        def __init__(self, value: str = "default") -> None:
            self.value = value

    instance = di.spawn(ServiceWithDefault)

    assert instance.value == "default"


def test_spawn_raises_when_required_dependency_not_resolved():
    di = DI()

    with pytest.raises(ValueError) as exc_info:
        di.spawn(DependentService)

    assert "Cannot resolve required dependency" in str(exc_info.value)
    assert "service" in str(exc_info.value)


def test_spawn_mixed_args_kwargs_and_resolved():
    di = DI()
    di.register(Service).factory(lambda: Service("resolved-service"))
    di.register(Counter).factory(lambda: Counter())

    instance = di.spawn(ComplexService, "manual-name")

    assert instance.name == "manual-name"
    assert instance.service.name == "resolved-service"
    assert instance.counter is not None
    assert instance.counter.value == 0
    assert instance.services == []
    assert instance.default_value == "default"


def test_spawn_override_resolved_with_kwargs():
    di = DI()
    di.register(Service).factory(lambda: Service("resolved-service"))
    manual_service = Service("manual-service")

    instance = di.spawn(DependentService, service=manual_service)

    assert instance.service is manual_service
    assert instance.service.name == "manual-service"


def test_spawn_resolves_multiple_services_for_list():
    di = DI()
    di.register(Service).factory(lambda: Service("first"))
    di.register(Service).factory(lambda: Service("second"))
    di.register(Service).factory(lambda: Service("third"))

    class MultiServiceConsumer:
        def __init__(self, services: List[Service]) -> None:
            self.services = services

    instance = di.spawn(MultiServiceConsumer)

    assert len(instance.services) == 3


def test_spawn_with_no_type_hints():
    di = DI()

    class NoHintsService:
        def __init__(self, value):  # type: ignore
            self.value = value

    instance = di.spawn(NoHintsService, "test-value")

    assert instance.value == "test-value"


def test_spawn_resolves_di_itself():
    di = DI()

    class ServiceWithDI:
        def __init__(self, di_instance: DI) -> None:
            self.di_instance = di_instance

    instance = di.spawn(ServiceWithDI)

    assert instance.di_instance is di


def test_spawn_with_string_annotations():
    di = DI()
    di.register(Service).factory(lambda: Service("resolved"))

    class ServiceWithStringAnnotation:
        def __init__(self, service: "Service") -> None:
            self.service = service

    instance = di.spawn(ServiceWithStringAnnotation)

    assert instance.service is not None
    assert instance.service.name == "resolved"

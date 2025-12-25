import pytest
import threading
from typing import List, Optional

from ps.plugin.core.di import _DI
from ps.plugin.sdk import DI


class Counter:
    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        self.value += 1


class Service:
    def __init__(self, name: str) -> None:
        self.name = name


class DependentService:
    def __init__(self, service: Service) -> None:
        self.service = service


class ComplexService:
    def __init__(
        self,
        name: str,
        service: Service,
        counter: Optional[Counter] = None,
        services: Optional[List[Service]] = None,
        default_value: str = "default",
    ) -> None:
        self.name = name
        self.service = service
        self.counter = counter
        self.services = services or []
        self.default_value = default_value


def test_singleton_returns_same_instance():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("test"))

    instance1 = di.resolve(Service)
    instance2 = di.resolve(Service)

    assert instance1 is not None
    assert instance2 is not None
    assert instance1 is instance2
    assert instance1.name == "test"


def test_transient_returns_different_instances():
    di = _DI()
    di.transient(Service).factory(lambda: Service("test"))

    instance1 = di.resolve(Service)
    instance2 = di.resolve(Service)

    assert instance1 is not None
    assert instance2 is not None
    assert instance1 is not instance2
    assert instance1.name == "test"
    assert instance2.name == "test"


def test_resolve_returns_none_when_not_registered():
    di = _DI()
    result = di.resolve(Service)
    assert result is None


def test_resolve_many_returns_empty_list_when_not_registered():
    di = _DI()
    result = di.resolve_many(Service)
    assert result == []


def test_resolve_many_returns_all_registrations():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("first"))
    di.singleton(Service).factory(lambda: Service("second"))
    di.singleton(Service).factory(lambda: Service("third"))

    services = di.resolve_many(Service)

    assert len(services) == 3
    assert services[0].name == "third"
    assert services[1].name == "second"
    assert services[2].name == "first"


def test_resolve_returns_most_recent_registration():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("first"))
    di.singleton(Service).factory(lambda: Service("second"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "second"


def test_singleton_with_implementation_type():
    di = _DI()

    class NoArgsService:
        pass

    di.singleton(NoArgsService).implementation(NoArgsService)

    service = di.resolve(NoArgsService)

    assert service is not None
    assert isinstance(service, NoArgsService)


def test_factory_with_arguments():
    di = _DI()
    di.singleton(Service).factory(Service, "custom-name")

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "custom-name"


def test_multiple_types_can_be_registered():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("service"))
    di.singleton(Counter).factory(lambda: Counter())

    service = di.resolve(Service)
    counter = di.resolve(Counter)

    assert service is not None
    assert counter is not None
    assert service.name == "service"
    assert counter.value == 0


def test_singleton_thread_safety():
    di = _DI()
    creation_count = Counter()

    def create_service() -> Service:
        creation_count.increment()
        return Service("thread-safe")

    di.singleton(Service).factory(create_service)

    instances: List[Service] = []
    lock = threading.Lock()

    def resolve_service() -> None:
        instance = di.resolve(Service)
        if instance is not None:
            with lock:
                instances.append(instance)

    threads = [threading.Thread(target=resolve_service) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(instances) == 10
    assert creation_count.value == 1
    assert all(instance is instances[0] for instance in instances)


def test_transient_creates_new_instances_in_concurrent_calls():
    di = _DI()
    di.transient(Service).factory(lambda: Service("transient"))

    instances: List[Service] = []
    lock = threading.Lock()

    def resolve_service() -> None:
        instance = di.resolve(Service)
        if instance is not None:
            with lock:
                instances.append(instance)

    threads = [threading.Thread(target=resolve_service) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(instances) == 10
    assert len({id(instance) for instance in instances}) == 10


def test_concurrent_registration_and_resolution():
    di = _DI()
    results: List[Service] = []
    lock = threading.Lock()

    def register_and_resolve(name: str) -> None:
        di.singleton(Service).factory(lambda n=name: Service(n))
        instance = di.resolve(Service)
        if instance is not None:
            with lock:
                results.append(instance)

    threads = [threading.Thread(target=register_and_resolve, args=(f"service-{i}",)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 5


def test_resolve_many_concurrent():
    di = _DI()
    for i in range(5):
        di.singleton(Service).factory(lambda idx=i: Service(f"service-{idx}"))

    results: List[List[Service]] = []
    lock = threading.Lock()

    def resolve_all() -> None:
        services = di.resolve_many(Service)
        with lock:
            results.append(services)

    threads = [threading.Thread(target=resolve_all) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 10
    assert all(len(services) == 5 for services in results)


def test_spawn_with_args_and_kwargs():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("from-di"))

    instance = di.spawn(Service, "manual-name")

    assert instance.name == "manual-name"


def test_spawn_with_kwargs():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("from-di"))

    instance = di.spawn(Service, name="manual-name")

    assert instance.name == "manual-name"


def test_spawn_resolves_simple_dependency():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("resolved-service"))

    instance = di.spawn(DependentService)

    assert instance.service is not None
    assert instance.service.name == "resolved-service"


def test_spawn_resolves_optional_dependency():
    di = _DI()
    di.singleton(Counter).factory(lambda: Counter())

    class ServiceWithOptional:
        def __init__(self, counter: Optional[Counter] = None) -> None:
            self.counter = counter

    instance = di.spawn(ServiceWithOptional)

    assert instance.counter is not None
    assert instance.counter.value == 0


def test_spawn_optional_dependency_not_registered():
    di = _DI()

    class ServiceWithOptional:
        def __init__(self, counter: Optional[Counter] = None) -> None:
            self.counter = counter

    instance = di.spawn(ServiceWithOptional)

    assert instance.counter is None


def test_spawn_resolves_list_dependency():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("service-1"))
    di.singleton(Service).factory(lambda: Service("service-2"))

    class ServiceWithList:
        def __init__(self, services: List[Service]) -> None:
            self.services = services

    instance = di.spawn(ServiceWithList)

    assert len(instance.services) == 2
    assert instance.services[0].name == "service-2"
    assert instance.services[1].name == "service-1"


def test_spawn_uses_default_value_when_dependency_not_resolved():
    di = _DI()

    class ServiceWithDefault:
        def __init__(self, value: str = "default") -> None:
            self.value = value

    instance = di.spawn(ServiceWithDefault)

    assert instance.value == "default"


def test_spawn_raises_when_required_dependency_not_resolved():
    di = _DI()

    with pytest.raises(ValueError) as exc_info:
        di.spawn(DependentService)

    assert "Cannot resolve required dependency" in str(exc_info.value)
    assert "service" in str(exc_info.value)


def test_spawn_mixed_args_kwargs_and_resolved():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("resolved-service"))
    di.singleton(Counter).factory(lambda: Counter())

    instance = di.spawn(ComplexService, "manual-name")

    assert instance.name == "manual-name"
    assert instance.service.name == "resolved-service"
    assert instance.counter is not None
    assert instance.counter.value == 0
    assert instance.services == []
    assert instance.default_value == "default"


def test_spawn_override_resolved_with_kwargs():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("resolved-service"))
    manual_service = Service("manual-service")

    instance = di.spawn(DependentService, service=manual_service)

    assert instance.service is manual_service
    assert instance.service.name == "manual-service"


def test_spawn_resolves_multiple_services_for_list():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("first"))
    di.singleton(Service).factory(lambda: Service("second"))
    di.singleton(Service).factory(lambda: Service("third"))

    class MultiServiceConsumer:
        def __init__(self, services: List[Service]) -> None:
            self.services = services

    instance = di.spawn(MultiServiceConsumer)

    assert len(instance.services) == 3


def test_spawn_with_no_type_hints():
    di = _DI()

    class NoHintsService:
        def __init__(self, value):  # type: ignore
            self.value = value

    instance = di.spawn(NoHintsService, "test-value")

    assert instance.value == "test-value"


def test_spawn_resolves_di_itself():
    di = _DI()

    class ServiceWithDI:
        def __init__(self, di_instance: DI) -> None:
            self.di_instance = di_instance

    instance = di.spawn(ServiceWithDI)

    assert instance.di_instance is di


def test_spawn_with_string_annotations():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("resolved"))

    # Manually create class with string annotation
    class ServiceWithStringAnnotation:
        def __init__(self, service: "Service") -> None:
            self.service = service

    instance = di.spawn(ServiceWithStringAnnotation)

    assert instance.service is not None
    assert instance.service.name == "resolved"


def test_register_and_resolve_with_string_type_name():
    di = _DI()

    # Register using the actual type first so it's in the registry
    di.singleton(Service).factory(lambda: Service("string-resolved"))

    # Resolve using string type name
    instance = di.resolve("Service")

    assert instance is not None
    assert instance.name == "string-resolved"


def test_resolve_many_with_string_type_name():
    di = _DI()
    di.singleton(Service).factory(lambda: Service("first"))
    di.singleton(Service).factory(lambda: Service("second"))

    services = di.resolve_many("Service")

    assert len(services) == 2
    assert services[0].name == "second"
    assert services[1].name == "first"


def test_resolve_string_type_not_registered():
    di = _DI()

    with pytest.raises(ValueError) as exc_info:
        di.resolve("NonExistent")

    assert "Cannot resolve type from string" in str(exc_info.value)
    assert "NonExistent" in str(exc_info.value)

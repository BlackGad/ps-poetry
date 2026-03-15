import pytest
import threading
from typing import List, Optional

from ps.di import DI, Binding, Lifetime, Priority, REQUIRED


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


def test_di_instantiation():
    di = DI()
    assert isinstance(di, DI)


def test_register_returns_binding():
    di = DI()
    binding = di.register(Service)
    assert isinstance(binding, Binding)


def test_singleton_returns_same_instance():
    di = DI()
    di.register(Service).factory(lambda: Service("test"))

    instance1 = di.resolve(Service)
    instance2 = di.resolve(Service)

    assert instance1 is not None
    assert instance2 is not None
    assert instance1 is instance2
    assert instance1.name == "test"


def test_transient_returns_different_instances():
    di = DI()
    di.register(Service, Lifetime.TRANSIENT).factory(lambda: Service("test"))

    instance1 = di.resolve(Service)
    instance2 = di.resolve(Service)

    assert instance1 is not None
    assert instance2 is not None
    assert instance1 is not instance2
    assert instance1.name == "test"
    assert instance2.name == "test"


def test_resolve_returns_none_when_not_registered():
    di = DI()
    result = di.resolve(Service)
    assert result is None


def test_resolve_many_returns_empty_list_when_not_registered():
    di = DI()
    result = di.resolve_many(Service)
    assert result == []


def test_resolve_many_returns_all_registrations():
    di = DI()
    di.register(Service).factory(lambda: Service("first"))
    di.register(Service).factory(lambda: Service("second"))
    di.register(Service).factory(lambda: Service("third"))

    services = di.resolve_many(Service)

    assert len(services) == 3
    assert services[0].name == "third"
    assert services[1].name == "second"
    assert services[2].name == "first"


def test_resolve_returns_most_recent_registration():
    di = DI()
    di.register(Service).factory(lambda: Service("first"))
    di.register(Service).factory(lambda: Service("second"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "second"


def test_singleton_with_implementation_type():
    di = DI()

    class NoArgsService:
        pass

    di.register(NoArgsService).implementation(NoArgsService)

    service = di.resolve(NoArgsService)

    assert service is not None
    assert isinstance(service, NoArgsService)


def test_factory_with_arguments():
    di = DI()
    di.register(Service).factory(Service, "custom-name")

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "custom-name"


def test_multiple_types_can_be_registered():
    di = DI()
    di.register(Service).factory(lambda: Service("service"))
    di.register(Counter).factory(lambda: Counter())

    service = di.resolve(Service)
    counter = di.resolve(Counter)

    assert service is not None
    assert counter is not None
    assert service.name == "service"
    assert counter.value == 0


def test_singleton_thread_safety():
    di = DI()
    creation_count = Counter()

    def create_service() -> Service:
        creation_count.increment()
        return Service("thread-safe")

    di.register(Service).factory(create_service)

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
    di = DI()
    di.register(Service, Lifetime.TRANSIENT).factory(lambda: Service("transient"))

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
    di = DI()
    results: List[Service] = []
    lock = threading.Lock()

    def register_and_resolve(name: str) -> None:
        di.register(Service).factory(lambda n=name: Service(n))
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
    di = DI()
    for i in range(5):
        di.register(Service).factory(lambda idx=i: Service(f"service-{idx}"))

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


def test_register_and_resolve_with_string_type_name():
    di = DI()

    di.register(Service).factory(lambda: Service("string-resolved"))

    instance = di.resolve("Service")

    assert instance is not None
    assert instance.name == "string-resolved"


def test_resolve_many_with_string_type_name():
    di = DI()
    di.register(Service).factory(lambda: Service("first"))
    di.register(Service).factory(lambda: Service("second"))

    services = di.resolve_many("Service")

    assert len(services) == 2
    assert services[0].name == "second"
    assert services[1].name == "first"


def test_resolve_string_type_not_registered():
    di = DI()

    with pytest.raises(ValueError) as exc_info:
        di.resolve("NonExistent")

    assert "Cannot resolve type from string" in str(exc_info.value)
    assert "NonExistent" in str(exc_info.value)


def test_priority_low_then_high():
    di = DI()
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("low-priority"))
    di.register(Service, priority=Priority.HIGH).factory(lambda: Service("high-priority"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "high-priority"


def test_priority_high_then_low():
    di = DI()
    di.register(Service, priority=Priority.HIGH).factory(lambda: Service("high-priority"))
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("low-priority"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "high-priority"


def test_priority_multiple_levels():
    di = DI()
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("low"))
    di.register(Service, priority=Priority.MEDIUM).factory(lambda: Service("medium"))
    di.register(Service, priority=Priority.HIGH).factory(lambda: Service("high"))
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("another-low"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "high"


def test_priority_same_priority_most_recent_wins():
    di = DI()
    di.register(Service, priority=Priority.MEDIUM).factory(lambda: Service("first-medium"))
    di.register(Service, priority=Priority.MEDIUM).factory(lambda: Service("second-medium"))
    di.register(Service, priority=Priority.MEDIUM).factory(lambda: Service("third-medium"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "third-medium"


def test_priority_resolve_many_returns_in_priority_order():
    di = DI()
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("low-1"))
    di.register(Service, priority=Priority.HIGH).factory(lambda: Service("high-1"))
    di.register(Service, priority=Priority.MEDIUM).factory(lambda: Service("medium-1"))
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("low-2"))
    di.register(Service, priority=Priority.HIGH).factory(lambda: Service("high-2"))

    services = di.resolve_many(Service)

    assert len(services) == 5
    assert services[0].name == "high-2"
    assert services[1].name == "high-1"
    assert services[2].name == "medium-1"
    assert services[3].name == "low-2"
    assert services[4].name == "low-1"


def test_priority_default_is_low():
    di = DI()
    di.register(Service).factory(lambda: Service("default-priority"))
    di.register(Service, priority=Priority.LOW).factory(lambda: Service("explicit-low"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "explicit-low"


def test_priority_with_different_lifetimes():
    di = DI()
    di.register(Service, lifetime=Lifetime.SINGLETON, priority=Priority.LOW).factory(lambda: Service("singleton-low"))
    di.register(Service, lifetime=Lifetime.TRANSIENT, priority=Priority.HIGH).factory(lambda: Service("transient-high"))

    service1 = di.resolve(Service)
    service2 = di.resolve(Service)

    assert service1 is not None
    assert service1.name == "transient-high"
    assert service1 is not service2


def test_priority_concurrent_registration():
    di = DI()

    def register_service(name: str, priority: Priority) -> None:
        di.register(Service, priority=priority).factory(lambda n=name: Service(n))

    threads = [
        threading.Thread(target=register_service, args=("low-1", Priority.LOW)),
        threading.Thread(target=register_service, args=("high-1", Priority.HIGH)),
        threading.Thread(target=register_service, args=("medium-1", Priority.MEDIUM)),
        threading.Thread(target=register_service, args=("low-2", Priority.LOW)),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    service = di.resolve(Service)
    assert service is not None
    assert "high" in service.name


def test_priority_mixed_with_default():
    di = DI()
    di.register(Service).factory(lambda: Service("default-1"))
    di.register(Service, priority=Priority.HIGH).factory(lambda: Service("high"))
    di.register(Service).factory(lambda: Service("default-2"))
    di.register(Service, priority=Priority.MEDIUM).factory(lambda: Service("medium"))

    service = di.resolve(Service)

    assert service is not None
    assert service.name == "high"

    services = di.resolve_many(Service)
    assert len(services) == 4
    assert services[0].name == "high"
    assert services[1].name == "medium"

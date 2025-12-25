import threading
from typing import List

from ps.plugin.core.di import _DI


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

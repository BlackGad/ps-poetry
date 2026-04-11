import threading
from typing import List

from ps.di import DI, Lifetime

from .conftest import Counter, Service


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

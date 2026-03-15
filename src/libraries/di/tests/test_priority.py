import threading

from ps.di import DI, Lifetime, Priority

from .conftest import Service


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

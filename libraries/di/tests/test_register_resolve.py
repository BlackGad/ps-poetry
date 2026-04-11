import pytest

from ps.di import DI, Binding

from .conftest import Counter, Service


def test_di_instantiation():
    di = DI()
    assert isinstance(di, DI)


def test_register_returns_binding():
    di = DI()
    binding = di.register(Service)
    assert isinstance(binding, Binding)


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

from ps.di import DI

from .conftest import Counter, Service


def test_context_manager_enter_returns_self():
    di = DI()
    with di as ctx:
        assert ctx is di


def test_context_manager_clears_registry_on_exit():
    di = DI()
    with di:
        di.register(Service).factory(lambda: Service("test"))
        assert di.resolve(Service) is not None

    assert di.resolve(Service) is None


def test_context_manager_releases_singleton_on_exit():
    di = DI()
    di.register(Counter).factory(Counter)

    with di:
        counter = di.resolve(Counter)
        assert counter is not None

    assert di.resolve(Counter) is None


def test_context_manager_clears_registrations_added_before_block():
    di = DI()
    di.register(Service).factory(lambda: Service("pre-block"))

    with di:
        assert di.resolve(Service) is not None

    assert di.resolve(Service) is None


def test_context_manager_container_reusable_after_exit():
    di = DI()

    with di:
        di.register(Service).factory(lambda: Service("first"))

    di.register(Service).factory(lambda: Service("second"))
    result = di.resolve(Service)

    assert result is not None
    assert result.name == "second"

from ps.di import DI

from .conftest import Counter, DependentService, Service


def test_scope_returns_di_instance():
    di = DI()
    scoped = di.scope()

    assert isinstance(scoped, DI)
    assert scoped is not di


def test_scope_resolves_parent_registration():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    result = scoped.resolve(Service)

    assert result is not None
    assert result.name == "parent"


def test_scope_resolve_returns_none_when_not_registered_anywhere():
    di = DI()
    scoped = di.scope()

    result = scoped.resolve(Service)

    assert result is None


def test_scope_own_registration_shadows_parent():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    result = scoped.resolve(Service)

    assert result is not None
    assert result.name == "scoped"


def test_scope_own_registration_does_not_affect_parent():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    parent_result = di.resolve(Service)
    assert parent_result is not None
    assert parent_result.name == "parent"


def test_scope_resolve_many_combines_parent_and_scoped():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    results = scoped.resolve_many(Service)
    names = [s.name for s in results]

    assert "scoped" in names
    assert "parent" in names
    assert len(results) == 2


def test_scope_resolve_many_scoped_first():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    results = scoped.resolve_many(Service)

    assert results[0].name == "scoped"
    assert results[1].name == "parent"


def test_scope_resolve_many_parent_only_when_no_scoped():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()

    results = scoped.resolve_many(Service)
    names = [s.name for s in results]

    assert names == ["parent"]


def test_scope_resolve_many_returns_empty_when_none_registered():
    di = DI()
    scoped = di.scope()

    results = scoped.resolve_many(Service)

    assert results == []


def test_scope_singleton_in_parent_shared_via_scope():
    di = DI()
    di.register(Counter).implementation(Counter)

    scoped = di.scope()

    counter_direct = di.resolve(Counter)
    counter_scoped = scoped.resolve(Counter)

    assert counter_direct is counter_scoped


def test_scope_singleton_in_scope_independent_of_parent():
    di = DI()
    di.register(Counter).implementation(Counter)

    scoped = di.scope()
    scoped.register(Counter).implementation(Counter)

    counter_parent = di.resolve(Counter)
    counter_scoped = scoped.resolve(Counter)

    assert counter_parent is not counter_scoped


def test_scope_spawn_uses_parent_dependencies():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    result = scoped.spawn(Counter)

    assert isinstance(result, Counter)


def test_scope_spawn_uses_scoped_dependencies():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    result = scoped.spawn(DependentService)

    assert result.service.name == "scoped"


def test_scope_string_resolution_falls_through_to_parent():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    result = scoped.resolve("Service")

    assert result is not None
    assert result.name == "parent"


def test_scope_string_resolution_uses_scoped_when_registered():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    result = scoped.resolve("Service")

    assert result is not None
    assert result.name == "scoped"


def test_nested_scope_resolves_grandparent():
    di = DI()
    di.register(Service).factory(lambda: Service("root"))

    child = di.scope()
    grandchild = child.scope()

    result = grandchild.resolve(Service)

    assert result is not None
    assert result.name == "root"


def test_nested_scope_shadows_parent():
    di = DI()
    di.register(Service).factory(lambda: Service("root"))

    child = di.scope()
    child.register(Service).factory(lambda: Service("child"))

    grandchild = child.scope()
    grandchild.register(Service).factory(lambda: Service("grandchild"))

    assert grandchild.resolve(Service).name == "grandchild"  # type: ignore[union-attr]
    assert child.resolve(Service).name == "child"  # type: ignore[union-attr]
    assert di.resolve(Service).name == "root"  # type: ignore[union-attr]


def test_scope_resolve_many_includes_all_levels():
    di = DI()
    di.register(Service).factory(lambda: Service("root"))

    child = di.scope()
    child.register(Service).factory(lambda: Service("child"))

    grandchild = child.scope()
    grandchild.register(Service).factory(lambda: Service("grandchild"))

    results = grandchild.resolve_many(Service)
    names = [s.name for s in results]

    assert names == ["grandchild", "child", "root"]


def test_scope_satisfy_uses_parent_di():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()

    def fn(service: Service) -> str:
        return service.name

    wrapper = scoped.satisfy(fn)
    result = wrapper()

    assert result == "parent"


def test_scope_satisfy_uses_scoped_di():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    def fn(service: Service) -> str:
        return service.name

    wrapper = scoped.satisfy(fn)
    result = wrapper()

    assert result == "scoped"


def test_scope_di_injection_provides_scoped_instance():
    di = DI()

    scoped = di.scope()

    def fn(container: DI) -> DI:
        return container

    wrapper = scoped.satisfy(fn)
    result = wrapper()

    assert result is scoped


def test_scope_resolve_many_parent_not_affected_by_scoped_registrations():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    scoped = di.scope()
    scoped.register(Service).factory(lambda: Service("scoped"))

    parent_results = di.resolve_many(Service)
    names = [s.name for s in parent_results]

    assert names == ["parent"]
    assert len(parent_results) == 1


def test_scope_context_manager_clears_scoped_registry():
    di = DI()

    with di.scope() as scoped:
        scoped.register(Service).factory(lambda: Service("scoped"))
        assert scoped.resolve(Service) is not None

    assert scoped.resolve(Service) is None


def test_scope_context_manager_parent_unaffected():
    di = DI()
    di.register(Service).factory(lambda: Service("parent"))

    with di.scope() as scoped:
        scoped.register(Service).factory(lambda: Service("scoped"))

    result = di.resolve(Service)
    assert result is not None
    assert result.name == "parent"


def test_context_manager_on_plain_di_clears_registry():
    di = DI()
    di.register(Service).factory(lambda: Service("test"))

    with di:
        assert di.resolve(Service) is not None

    assert di.resolve(Service) is None


def test_scope_context_manager_returns_di_instance():
    di = DI()

    with di.scope() as scoped:
        assert isinstance(scoped, DI)

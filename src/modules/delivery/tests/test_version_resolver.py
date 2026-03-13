from ps.version import Version

from ps.plugin.module.delivery.token_resolvers._version_resolver import VersionResolver


def test_version_resolver_no_args_returns_none():
    resolver = VersionResolver()
    assert resolver([]) is None


def test_version_resolver_invalid_string_returns_none():
    resolver = VersionResolver()
    assert resolver(["not-a-version"]) is None


def test_version_resolver_valid_string_no_accessor_returns_str():
    resolver = VersionResolver()
    result = resolver(["1.2.3"])
    assert result == "1.2.3"


def test_version_resolver_major_accessor():
    resolver = VersionResolver()
    assert resolver(["1.2.3", "major"]) == 1


def test_version_resolver_minor_accessor():
    resolver = VersionResolver()
    assert resolver(["1.2.3", "minor"]) == 2


def test_version_resolver_patch_accessor():
    resolver = VersionResolver()
    assert resolver(["1.2.3", "patch"]) == 3


def test_version_resolver_core_accessor():
    resolver = VersionResolver()
    assert resolver(["1.2.3", "core"]) == "1.2.3"


def test_version_resolver_unknown_accessor_returns_none():
    resolver = VersionResolver()
    assert resolver(["1.2.3", "unknown_field"]) is None


def test_version_resolver_empty_string_returns_none():
    resolver = VersionResolver()
    assert resolver([""]) is None


def test_version_resolver_major_only_version():
    resolver = VersionResolver()
    assert resolver(["5", "major"]) == 5


def test_version_resolver_prerelease_version_str():
    resolver = VersionResolver()
    result = resolver(["2.0.0a1"])
    assert result is not None
    assert Version.parse(str(result)) is not None

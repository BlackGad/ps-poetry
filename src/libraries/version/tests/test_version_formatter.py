from ps.version import Version, VersionFormatter, VersionMetadata, VersionPreRelease, VersionStandard


def test_format_property_returns_formatter_instance():
    version = Version(major=1, minor=2, patch=3)
    assert isinstance(version.format, VersionFormatter)


def test_format_property_holds_correct_version():
    version = Version(major=1, minor=2, patch=3)
    assert version.format.version is version


# ---------------------------------------------------------------------------
# __call__ — pep440
# ---------------------------------------------------------------------------

def test_call_pep440_simple():
    version = Version(major=1, minor=2, patch=3)
    assert version.format(VersionStandard.PEP440) == "1.2.3"


def test_call_pep440_with_prerelease():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="a", number=1))
    assert version.format(VersionStandard.PEP440) == "1.2.3a1"


def test_call_pep440_with_post():
    version = Version(major=1, minor=2, patch=3, post=4)
    assert version.format(VersionStandard.PEP440) == "1.2.3.post4"


def test_call_pep440_with_dev():
    version = Version(major=1, minor=2, patch=3, dev=1)
    assert version.format(VersionStandard.PEP440) == "1.2.3.dev1"


def test_call_pep440_with_metadata():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("g1234567"))
    assert version.format(VersionStandard.PEP440) == "1.2.3+g1234567"


def test_call_pep440_complex():
    version = Version(major=1, minor=2, patch=3, post=4, metadata=VersionMetadata("g1234567.dirty"))
    assert version.format(VersionStandard.PEP440) == "1.2.3.post4+g1234567.dirty"


# ---------------------------------------------------------------------------
# __call__ — semver
# ---------------------------------------------------------------------------

def test_call_semver_simple():
    version = Version(major=1, minor=2, patch=3)
    assert version.format(VersionStandard.SEMVER) == "1.2.3"


def test_call_semver_with_prerelease():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="alpha", number=1))
    assert version.format(VersionStandard.SEMVER) == "1.2.3-alpha.1"


def test_call_semver_with_metadata():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("build.123"))
    assert version.format(VersionStandard.SEMVER) == "1.2.3+build.123"


def test_call_semver_full():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="rc", number=1), metadata=VersionMetadata("build.123"))
    assert version.format(VersionStandard.SEMVER) == "1.2.3-rc.1+build.123"


# ---------------------------------------------------------------------------
# __call__ — nuget
# ---------------------------------------------------------------------------

def test_call_nuget_simple():
    version = Version(major=1, minor=2, patch=3)
    assert version.format(VersionStandard.NUGET) == "1.2.3"


def test_call_nuget_with_rev():
    version = Version(major=1, minor=2, patch=3, rev=4)
    assert version.format(VersionStandard.NUGET) == "1.2.3.4"


def test_call_nuget_with_prerelease():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="beta", number=1))
    assert version.format(VersionStandard.NUGET) == "1.2.3-beta.1"


# ---------------------------------------------------------------------------
# __call__ — calver
# ---------------------------------------------------------------------------

def test_call_calver_simple():
    version = Version(major=2024, minor=1, patch=0)
    assert version.format(VersionStandard.CALVER) == "2024.1.0"


def test_call_calver_with_metadata():
    version = Version(major=2024, minor=3, patch=1, metadata=VersionMetadata("release"))
    assert version.format(VersionStandard.CALVER) == "2024.3.1-release"


# ---------------------------------------------------------------------------
# __call__ — loose
# ---------------------------------------------------------------------------

def test_call_loose_simple():
    version = Version(major=1, minor=2, patch=3)
    assert version.format(VersionStandard.LOOSE) == "1.2.3"


def test_call_loose_with_metadata():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("custom"))
    assert version.format(VersionStandard.LOOSE) == "1.2.3-custom"


# ---------------------------------------------------------------------------
# __call__ — unknown standard falls back to pep440
# ---------------------------------------------------------------------------

def test_call_unknown_standard_falls_back_to_pep440():
    version = Version(major=1, minor=2, patch=3, post=1)
    formatter = VersionFormatter(version)
    result = formatter(VersionStandard.PEP440)
    assert result == formatter.pep440


# ---------------------------------------------------------------------------
# property shortcuts
# ---------------------------------------------------------------------------

def test_pep440_property():
    version = Version(major=1, minor=2, patch=3)
    assert version.format.pep440 == "1.2.3"


def test_semver_property():
    version = Version(major=1, minor=2, patch=3)
    assert version.format.semver == "1.2.3"


def test_nuget_property():
    version = Version(major=1, minor=2, patch=3, rev=4)
    assert version.format.nuget == "1.2.3.4"


def test_calver_property():
    version = Version(major=2024, minor=6, patch=15)
    assert version.format.calver == "2024.6.15"


def test_loose_property():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("local"))
    assert version.format.loose == "1.2.3-local"

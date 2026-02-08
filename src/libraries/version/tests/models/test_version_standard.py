from ps.version import VersionStandard


def test_enum_values():
    assert VersionStandard.PEP440.value == "pep440"
    assert VersionStandard.SEMVER.value == "semver"
    assert VersionStandard.NUGET.value == "nuget"
    assert VersionStandard.CALVER.value == "calver"
    assert VersionStandard.LOOSE.value == "loose"
    assert VersionStandard.UNKNOWN.value == "unknown"


def test_enum_members():
    standards = list(VersionStandard)
    assert len(standards) == 6
    assert VersionStandard.PEP440 in standards
    assert VersionStandard.SEMVER in standards
    assert VersionStandard.NUGET in standards
    assert VersionStandard.CALVER in standards
    assert VersionStandard.LOOSE in standards
    assert VersionStandard.UNKNOWN in standards

from ps.version import Version, VersionMetadata, VersionPreRelease, VersionStandard

import pytest


def test_version_accepts_metadata_object():
    meta = VersionMetadata("build.123")
    version = Version(major=1, metadata=meta)
    assert version.metadata is meta
    assert str(version.metadata) == "build.123"


def test_default_values():
    version = Version(major=0)
    assert version.major == 0
    assert version.minor is None
    assert version.patch is None
    assert version.rev is None
    assert version.pre is None
    assert version.post is None
    assert version.dev is None
    assert version.metadata is None
    assert VersionStandard.LOOSE in version.standards
    assert VersionStandard.PEP440 in version.standards


def test_core_property_three_parts():
    version = Version(major=1, minor=2, patch=3)
    assert version.core == "1.2.3"


def test_core_property_four_parts():
    version = Version(major=1, minor=2, patch=3, rev=4)
    assert version.core == "1.2.3.4"


def test_core_property_zero_rev():
    version = Version(major=1, minor=2, patch=3, rev=0)
    assert version.core == "1.2.3"


def test_version_str_simple():
    version = Version(major=1, minor=2, patch=3)
    assert version.format(VersionStandard.PEP440) == "1.2.3"


def test_version_str_pep440_with_prerelease():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="a", number=1))
    assert version.format(VersionStandard.PEP440) == "1.2.3a1"


def test_version_str_semver_with_prerelease():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="alpha", number=1))
    assert version.format(VersionStandard.SEMVER) == "1.2.3-alpha.1"


def test_version_str_pep440_with_post():
    version = Version(major=1, minor=2, patch=3, post=4)
    assert version.format(VersionStandard.PEP440) == "1.2.3.post4"


def test_version_str_pep440_with_dev():
    version = Version(major=1, minor=2, patch=3, dev=1)
    assert version.format(VersionStandard.PEP440) == "1.2.3.dev1"


def test_version_str_pep440_with_metadata():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("g1234567"))
    assert version.format(VersionStandard.PEP440) == "1.2.3+g1234567"


def test_version_str_pep440_complex():
    version = Version(major=1, minor=2, patch=3, post=4, metadata=VersionMetadata("g1234567.dirty"))
    assert version.format(VersionStandard.PEP440) == "1.2.3.post4+g1234567.dirty"


def test_version_str_semver_with_metadata():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("build.123"))
    assert version.format(VersionStandard.SEMVER) == "1.2.3+build.123"


def test_version_str_semver_full():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="rc", number=1), metadata=VersionMetadata("build.123"))
    assert version.format(VersionStandard.SEMVER) == "1.2.3-rc.1+build.123"


def test_version_str_nuget_with_rev():
    version = Version(major=1, minor=2, patch=3, rev=4)
    assert version.format(VersionStandard.NUGET) == "1.2.3.4"


def test_version_str_nuget_with_prerelease():
    version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="beta", number=1))
    assert version.format(VersionStandard.NUGET) == "1.2.3-beta.1"


def test_version_str_calver():
    version = Version(major=2024, minor=1, patch=0)
    assert version.format(VersionStandard.CALVER) == "2024.1.0"


def test_version_str_loose_with_metadata():
    version = Version(major=1, minor=2, patch=3, metadata=VersionMetadata("custom"))
    assert version.format(VersionStandard.LOOSE) == "1.2.3-custom"


def test_meta_single_part():
    version = Version(major=0, metadata=VersionMetadata("build"))
    assert version.metadata
    assert version.metadata.parts[0] == "build"
    assert len(version.metadata.parts) == 1


def test_meta_multiple_parts():
    version = Version(major=0, metadata=VersionMetadata("g1234567.dirty"))
    assert version.metadata
    assert version.metadata.parts[0] == "g1234567"
    assert version.metadata.parts[1] == "dirty"


def test_meta_empty():
    version = Version(major=0, metadata=None)
    assert version.metadata is None


def test_meta_three_parts():
    version = Version(major=0, metadata=VersionMetadata("part1.part2.part3"))
    assert version.metadata
    assert version.metadata.parts[0] == "part1"
    assert version.metadata.parts[1] == "part2"
    assert version.metadata.parts[2] == "part3"
    assert len(version.metadata.parts) == 3


def test_meta_str_conversion():
    version = Version(major=0, metadata=VersionMetadata("g1234567.dirty"))
    assert version.metadata
    assert str(version.metadata) == "g1234567.dirty"


def test_meta_parts_property():
    version = Version(major=0, metadata=VersionMetadata("build"))
    assert version.metadata
    assert len(version.metadata.parts) == 1


def test_version_negative_major_raises_error():
    with pytest.raises(ValueError, match="major must be non-negative"):
        Version(major=-1)


def test_version_negative_minor_raises_error():
    with pytest.raises(ValueError, match="minor must be non-negative"):
        Version(major=1, minor=-1)


def test_version_negative_patch_raises_error():
    with pytest.raises(ValueError, match="patch must be non-negative"):
        Version(major=1, minor=2, patch=-1)


def test_version_negative_rev_raises_error():
    with pytest.raises(ValueError, match="rev must be non-negative"):
        Version(major=1, minor=2, patch=3, rev=-1)


def test_version_negative_post_raises_error():
    with pytest.raises(ValueError, match="post must be non-negative"):
        Version(major=1, post=-1)


def test_version_negative_dev_raises_error():
    with pytest.raises(ValueError, match="dev must be non-negative"):
        Version(major=1, dev=-1)

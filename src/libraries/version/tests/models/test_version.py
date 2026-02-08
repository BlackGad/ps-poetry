from ps.version import PreRelease, Version, VersionStandard


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
    assert version.standard == VersionStandard.UNKNOWN
    assert version.raw is None


def test_core_property_three_parts():
    version = Version(major=1, minor=2, patch=3)
    assert version.core == "1.2.3"


def test_core_property_four_parts():
    version = Version(major=1, minor=2, patch=3, rev=4)
    assert version.core == "1.2.3.4"


def test_core_property_zero_rev():
    version = Version(major=1, minor=2, patch=3, rev=0)
    assert version.core == "1.2.3"


def test_pre_property_with_label_and_number():
    version = Version(major=0, pre=PreRelease(name="alpha", number=1))
    assert version.pre_text == "alpha1"


def test_pre_property_with_label_only():
    version = Version(major=0, pre=PreRelease(name="beta", number=None))
    assert version.pre_text == "beta"


def test_pre_property_empty():
    version = Version(major=0)
    assert version.pre_text == ""


def test_meta_single_part():
    version = Version(major=0, metadata="build")
    assert version.meta(0) == "build"
    assert version.meta(1) is None


def test_meta_multiple_parts():
    version = Version(major=0, metadata="g1234567.dirty")
    assert version.meta(0) == "g1234567"
    assert version.meta(1) == "dirty"


def test_meta_empty():
    version = Version(major=0, metadata=None)
    assert version.meta(0) is None
    assert version.meta(1) is None


def test_meta_three_parts():
    version = Version(major=0, metadata="part1.part2.part3")
    assert version.meta(0) == "part1"
    assert version.meta(1) == "part2.part3"

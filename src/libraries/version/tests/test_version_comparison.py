from ps.version import Version, VersionPreRelease


def test_version_equality_simple():
    v1 = Version(major=1, minor=2, patch=3)
    v2 = Version(major=1, minor=2, patch=3)
    assert v1 == v2


def test_version_equality_different():
    v1 = Version(major=1, minor=2, patch=3)
    v2 = Version(major=1, minor=2, patch=4)
    assert v1 != v2


def test_version_less_than_major():
    v1 = Version(major=1, minor=2, patch=3)
    v2 = Version(major=2, minor=0, patch=0)
    assert v1 < v2
    assert not v2 < v1


def test_version_less_than_minor():
    v1 = Version(major=1, minor=2, patch=3)
    v2 = Version(major=1, minor=3, patch=0)
    assert v1 < v2
    assert not v2 < v1


def test_version_less_than_patch():
    v1 = Version(major=1, minor=2, patch=3)
    v2 = Version(major=1, minor=2, patch=4)
    assert v1 < v2
    assert not v2 < v1


def test_version_less_than_rev():
    v1 = Version(major=1, minor=2, patch=3, rev=1)
    v2 = Version(major=1, minor=2, patch=3, rev=2)
    assert v1 < v2
    assert not v2 < v1


def test_version_with_pre_less_than_without():
    v1 = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="alpha", number=1))
    v2 = Version(major=1, minor=2, patch=3)
    assert v1 < v2
    assert not v2 < v1


def test_version_pre_alphabetical():
    v1 = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="alpha", number=1))
    v2 = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="beta", number=1))
    assert v1 < v2
    assert not v2 < v1


def test_version_pre_number():
    v1 = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="alpha", number=1))
    v2 = Version(major=1, minor=2, patch=3, pre=VersionPreRelease(name="alpha", number=2))
    assert v1 < v2
    assert not v2 < v1


def test_version_pep440_dev_less_than_pre():
    v1 = Version(major=1, minor=0, patch=0, dev=1)
    v2 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="a", number=1))
    assert v1 < v2
    assert not v2 < v1


def test_version_pep440_dev_less_than_normal():
    v1 = Version(major=1, minor=0, patch=0, dev=1)
    v2 = Version(major=1, minor=0, patch=0)
    assert v1 < v2
    assert not v2 < v1


def test_version_pep440_post_greater_than_normal():
    v1 = Version(major=1, minor=0, patch=0)
    v2 = Version(major=1, minor=0, patch=0, post=1)
    assert v1 < v2
    assert not v2 < v1


def test_version_pep440_post_numbers():
    v1 = Version(major=1, minor=0, patch=0, post=1)
    v2 = Version(major=1, minor=0, patch=0, post=2)
    assert v1 < v2
    assert not v2 < v1


def test_version_greater_than():
    v1 = Version(major=2, minor=0, patch=0)
    v2 = Version(major=1, minor=0, patch=0)
    assert v1 > v2
    assert not v2 > v1


def test_version_greater_equal():
    v1 = Version(major=2, minor=0, patch=0)
    v2 = Version(major=1, minor=0, patch=0)
    v3 = Version(major=2, minor=0, patch=0)
    assert v1 >= v2
    assert v1 >= v3
    assert not v2 >= v1


def test_version_less_equal():
    v1 = Version(major=1, minor=0, patch=0)
    v2 = Version(major=2, minor=0, patch=0)
    v3 = Version(major=1, minor=0, patch=0)
    assert v1 <= v2
    assert v1 <= v3
    assert not v2 <= v1


def test_version_pep440_full_order():
    v_dev = Version(major=1, minor=0, patch=0, dev=1)
    v_alpha = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="a", number=1))
    v_beta = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="b", number=1))
    v_rc = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="rc", number=1))
    v_normal = Version(major=1, minor=0, patch=0)
    v_post = Version(major=1, minor=0, patch=0, post=1)

    assert v_dev < v_alpha < v_beta < v_rc < v_normal < v_post


def test_version_semver_pre_order():
    v_alpha1 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="alpha", number=1))
    v_alpha2 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="alpha", number=2))
    v_beta = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="beta", number=1))
    v_normal = Version(major=1, minor=0, patch=0)

    assert v_alpha1 < v_alpha2 < v_beta < v_normal


def test_version_none_fields_treated_as_zero():
    v1 = Version(major=1, minor=None, patch=None)
    v2 = Version(major=1, minor=0, patch=0)
    assert v1 == v2


def test_version_pre_case_insensitive():
    v1 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="Alpha", number=1))
    v2 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="alpha", number=1))
    v3 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="ALPHA", number=1))
    assert v1 == v2
    assert v2 == v3


def test_version_pre_case_insensitive_comparison():
    v1 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="Alpha", number=1))
    v2 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="Beta", number=1))
    v3 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="beta", number=1))
    assert v1 < v2
    assert v1 < v3
    assert v2 == v3


def test_version_pre_case_insensitive_hash():
    v1 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="Alpha", number=1))
    v2 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="alpha", number=1))
    v3 = Version(major=1, minor=0, patch=0, pre=VersionPreRelease(name="ALPHA", number=1))
    assert hash(v1) == hash(v2)
    assert hash(v2) == hash(v3)

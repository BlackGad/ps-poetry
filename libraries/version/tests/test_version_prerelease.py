from ps.version import VersionPreRelease

import pytest


def test_prerelease_str_with_label_and_number():
    pre = VersionPreRelease(name="alpha", number=1)
    assert str(pre) == "alpha1"


def test_prerelease_str_with_label_only():
    pre = VersionPreRelease(name="beta", number=None)
    assert str(pre) == "beta"


def test_prerelease_str_with_zero_number():
    pre = VersionPreRelease(name="alpha", number=0)
    assert str(pre) == "alpha0"


def test_prerelease_negative_number_raises_error():
    with pytest.raises(ValueError, match="Pre-release number must be non-negative"):
        VersionPreRelease(name="alpha", number=-1)


def test_prerelease_equality():
    pre1 = VersionPreRelease(name="alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="alpha", number=2)
    pre4 = VersionPreRelease(name="beta", number=1)
    assert pre1 == pre2
    assert pre1 != pre3
    assert pre1 != pre4


def test_prerelease_equality_none_number():
    pre1 = VersionPreRelease(name="alpha", number=None)
    pre2 = VersionPreRelease(name="alpha", number=0)
    assert pre1 == pre2


def test_prerelease_less_than_by_name():
    pre1 = VersionPreRelease(name="alpha", number=1)
    pre2 = VersionPreRelease(name="beta", number=1)
    assert pre1 < pre2
    assert not pre2 < pre1


def test_prerelease_less_than_by_number():
    pre1 = VersionPreRelease(name="alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=2)
    assert pre1 < pre2
    assert not pre2 < pre1


def test_prerelease_greater_than():
    pre1 = VersionPreRelease(name="beta", number=2)
    pre2 = VersionPreRelease(name="alpha", number=1)
    assert pre1 > pre2
    assert not pre2 > pre1


def test_prerelease_less_equal():
    pre1 = VersionPreRelease(name="alpha", number=1)
    pre2 = VersionPreRelease(name="beta", number=1)
    pre3 = VersionPreRelease(name="alpha", number=1)
    assert pre1 <= pre2
    assert pre1 <= pre3
    assert not pre2 <= pre1


def test_prerelease_greater_equal():
    pre1 = VersionPreRelease(name="beta", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="beta", number=1)
    assert pre1 >= pre2
    assert pre1 >= pre3
    assert not pre2 >= pre1


def test_prerelease_hash():
    pre1 = VersionPreRelease(name="alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="alpha", number=2)
    assert hash(pre1) == hash(pre2)
    assert hash(pre1) != hash(pre3)


def test_prerelease_in_set():
    pre1 = VersionPreRelease(name="alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="beta", number=1)
    pre_set = {pre1, pre2, pre3}
    assert len(pre_set) == 2


def test_prerelease_case_insensitive_equality():
    pre1 = VersionPreRelease(name="Alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="ALPHA", number=1)
    assert pre1 == pre2
    assert pre2 == pre3


def test_prerelease_case_insensitive_comparison():
    pre1 = VersionPreRelease(name="Alpha", number=1)
    pre2 = VersionPreRelease(name="Beta", number=1)
    pre3 = VersionPreRelease(name="beta", number=1)
    assert pre1 < pre2
    assert pre1 < pre3
    assert pre2 == pre3


def test_prerelease_case_insensitive_hash():
    pre1 = VersionPreRelease(name="Alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="ALPHA", number=1)
    assert hash(pre1) == hash(pre2)
    assert hash(pre2) == hash(pre3)


def test_prerelease_case_insensitive_in_set():
    pre1 = VersionPreRelease(name="Alpha", number=1)
    pre2 = VersionPreRelease(name="alpha", number=1)
    pre3 = VersionPreRelease(name="ALPHA", number=1)
    pre_set = {pre1, pre2, pre3}
    assert len(pre_set) == 1

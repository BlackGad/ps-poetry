from ps.version import VersionMetadata


def test_metadata_str():
    meta = VersionMetadata("g1234567.dirty")
    assert str(meta) == "g1234567.dirty"


def test_metadata_call_with_index():
    meta = VersionMetadata("g1234567.dirty")
    assert meta(0) == "g1234567"
    assert meta(1) == "dirty"


def test_metadata_call_no_index():
    meta = VersionMetadata("g1234567.dirty")
    assert meta() == "g1234567.dirty"


def test_metadata_call_negative_index():
    meta = VersionMetadata("build")
    assert meta(-1) is None


def test_metadata_single_part():
    meta = VersionMetadata("build")
    assert meta(0) == "build"
    assert meta(1) is None


def test_metadata_multiple_parts():
    meta = VersionMetadata("g1234567.dirty")
    assert meta(0) == "g1234567"
    assert meta(1) == "dirty"


def test_metadata_three_parts():
    meta = VersionMetadata("part1.part2.part3")
    assert meta(0) == "part1"
    assert meta(1) == "part2"
    assert meta(2) == "part3"
    assert meta(3) is None


def test_metadata_many_parts():
    meta = VersionMetadata("a.b.c.d.e.f")
    assert meta(0) == "a"
    assert meta(1) == "b"
    assert meta(2) == "c"
    assert meta(3) == "d"
    assert meta(4) == "e"
    assert meta(5) == "f"
    assert meta(6) is None


def test_metadata_equality():
    meta1 = VersionMetadata("build.123")
    meta2 = VersionMetadata("build.123")
    meta3 = VersionMetadata("build.124")
    assert meta1 == meta2
    assert meta1 != meta3


def test_metadata_less_than():
    meta1 = VersionMetadata("alpha")
    meta2 = VersionMetadata("beta")
    assert meta1 < meta2
    assert not meta2 < meta1


def test_metadata_greater_than():
    meta1 = VersionMetadata("beta")
    meta2 = VersionMetadata("alpha")
    assert meta1 > meta2
    assert not meta2 > meta1


def test_metadata_less_equal():
    meta1 = VersionMetadata("alpha")
    meta2 = VersionMetadata("beta")
    meta3 = VersionMetadata("alpha")
    assert meta1 <= meta2
    assert meta1 <= meta3
    assert not meta2 <= meta1


def test_metadata_greater_equal():
    meta1 = VersionMetadata("beta")
    meta2 = VersionMetadata("alpha")
    meta3 = VersionMetadata("beta")
    assert meta1 >= meta2
    assert meta1 >= meta3
    assert not meta2 >= meta1


def test_metadata_hash():
    meta1 = VersionMetadata("build.123")
    meta2 = VersionMetadata("build.123")
    meta3 = VersionMetadata("build.124")
    assert hash(meta1) == hash(meta2)
    assert hash(meta1) != hash(meta3)


def test_metadata_in_set():
    meta1 = VersionMetadata("build.123")
    meta2 = VersionMetadata("build.123")
    meta3 = VersionMetadata("build.124")
    meta_set = {meta1, meta2, meta3}
    assert len(meta_set) == 2

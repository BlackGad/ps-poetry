from ps.version import ParsedVersion, VersionStandard


class TestParsedVersion:
    def test_default_values(self):
        version = ParsedVersion()
        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 0
        assert version.rev == 0
        assert version.pre_label == ""
        assert version.pre_num == 0
        assert version.post == 0
        assert version.dev == 0
        assert version.meta == ""
        assert version.standard == VersionStandard.UNKNOWN
        assert version.raw == ""

    def test_core_property_three_parts(self):
        version = ParsedVersion(major=1, minor=2, patch=3)
        assert version.core == "1.2.3"

    def test_core_property_four_parts(self):
        version = ParsedVersion(major=1, minor=2, patch=3, rev=4)
        assert version.core == "1.2.3.4"

    def test_core_property_zero_rev(self):
        version = ParsedVersion(major=1, minor=2, patch=3, rev=0)
        assert version.core == "1.2.3"

    def test_pre_property_with_label_and_number(self):
        version = ParsedVersion(pre_label="alpha", pre_num=1)
        assert version.pre == "alpha1"

    def test_pre_property_with_label_only(self):
        version = ParsedVersion(pre_label="beta", pre_num=0)
        assert version.pre == "beta"

    def test_pre_property_empty(self):
        version = ParsedVersion()
        assert version.pre == ""

    def test_meta0_property_single_part(self):
        version = ParsedVersion(meta="build")
        assert version.meta0 == "build"
        assert version.meta1 == ""

    def test_meta0_property_multiple_parts(self):
        version = ParsedVersion(meta="g1234567.dirty")
        assert version.meta0 == "g1234567"
        assert version.meta1 == "dirty"

    def test_meta1_property_empty(self):
        version = ParsedVersion(meta="")
        assert version.meta0 == ""
        assert version.meta1 == ""

    def test_meta1_property_three_parts(self):
        version = ParsedVersion(meta="part1.part2.part3")
        assert version.meta0 == "part1"
        assert version.meta1 == "part2.part3"

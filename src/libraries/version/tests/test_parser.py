from ps.version import VersionParser, VersionStandard


class TestVersionParser:
    def test_parse_empty_string(self):
        result = VersionParser.parse("")
        assert result.major == 0
        assert result.minor == 0
        assert result.patch == 0

    def test_parse_invalid_version(self):
        result = VersionParser.parse("invalid")
        assert result.standard == VersionStandard.UNKNOWN

    def test_parse_with_whitespace(self):
        result = VersionParser.parse("  1.2.3  ")
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3

    def test_parse_zero_version(self):
        result = VersionParser.parse("0.0.0")
        assert result.major == 0
        assert result.minor == 0
        assert result.patch == 0

    def test_parse_pep440_simple(self):
        result = VersionParser.parse("1.2.3")
        assert result.standard == VersionStandard.PEP440
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3

    def test_parse_pep440_complex(self):
        result = VersionParser.parse("1.2.3.post4+g1234567.dirty")
        assert result.standard == VersionStandard.PEP440
        assert result.major == 1
        assert result.post == 4
        assert result.meta == "g1234567.dirty"

    def test_parse_semver_prerelease(self):
        result = VersionParser.parse("1.2.3-alpha.1")
        assert result.standard == VersionStandard.SEMVER
        assert result.pre_label == "alpha"
        assert result.pre_num == 1

    def test_parse_nuget_four_part(self):
        result = VersionParser.parse("1.2.3.4")
        assert result.rev == 4

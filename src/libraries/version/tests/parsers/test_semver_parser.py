from ps.version.models import VersionStandard
from ps.version.parsers import SemVerParser


class TestSemVerParser:
    def setup_method(self):
        self.parser = SemVerParser()

    def test_parse_simple_version(self):
        result = self.parser.parse("1.2.3")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.standard == VersionStandard.SEMVER

    def test_parse_prerelease(self):
        result = self.parser.parse("1.2.3-alpha.1")
        assert result is not None
        assert result.pre_label == "alpha"
        assert result.pre_num == 1

    def test_parse_with_build(self):
        result = self.parser.parse("1.2.3+build.123")
        assert result is not None
        assert result.meta == "build.123"

    def test_parse_full(self):
        result = self.parser.parse("1.2.3-rc.1+build.123")
        assert result is not None
        assert result.pre_label == "rc"
        assert result.pre_num == 1
        assert result.meta == "build.123"

    def test_reject_two_part_version(self):
        result = self.parser.parse("1.2")
        assert result is None

    def test_reject_pep440_format(self):
        result = self.parser.parse("1.2.3.post1")
        assert result is None

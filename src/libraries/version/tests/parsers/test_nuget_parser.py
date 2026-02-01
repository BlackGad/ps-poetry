from ps.version.models import VersionStandard
from ps.version.parsers import NuGetParser


class TestNuGetParser:
    def setup_method(self):
        self.parser = NuGetParser()

    def test_parse_three_part_version(self):
        result = self.parser.parse("1.2.3")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.standard == VersionStandard.NUGET

    def test_parse_four_part_version(self):
        result = self.parser.parse("1.2.3.4")
        assert result is not None
        assert result.rev == 4

    def test_parse_prerelease(self):
        result = self.parser.parse("1.2.3-beta")
        assert result is not None
        assert result.pre_label == "beta"

    def test_parse_prerelease_with_number(self):
        result = self.parser.parse("1.2.3-beta.1")
        assert result is not None
        assert result.pre_label == "beta"
        assert result.pre_num == 1

    def test_reject_two_part_version(self):
        result = self.parser.parse("1.2")
        assert result is None

    def test_reject_with_build_metadata(self):
        result = self.parser.parse("1.2.3+build")
        assert result is None

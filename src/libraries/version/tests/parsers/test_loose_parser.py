from ps.version.models import VersionStandard
from ps.version.parsers import LooseParser


class TestLooseParser:
    def setup_method(self):
        self.parser = LooseParser()

    def test_parse_single_number(self):
        result = self.parser.parse("1")
        assert result is not None
        assert result.major == 1
        assert result.minor == 0
        assert result.standard == VersionStandard.LOOSE

    def test_parse_two_numbers(self):
        result = self.parser.parse("1.2")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2

    def test_parse_three_numbers(self):
        result = self.parser.parse("1.2.3")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3

    def test_parse_with_suffix(self):
        result = self.parser.parse("1.2.3-custom")
        assert result is not None
        assert result.meta == "custom"

    def test_reject_invalid(self):
        result = self.parser.parse("invalid")
        assert result is None

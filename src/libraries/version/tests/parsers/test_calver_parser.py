from ps.version.models import VersionStandard
from ps.version.parsers import CalVerParser


class TestCalVerParser:
    def setup_method(self):
        self.parser = CalVerParser()

    def test_parse_full_year(self):
        result = self.parser.parse("2024.1.0")
        assert result is not None
        assert result.major == 2024
        assert result.minor == 1
        assert result.patch == 0
        assert result.standard == VersionStandard.CALVER

    def test_parse_short_year(self):
        result = self.parser.parse("24.1.0")
        assert result is not None
        assert result.major == 24

    def test_parse_date_format(self):
        result = self.parser.parse("2024.12.31")
        assert result is not None
        assert result.major == 2024
        assert result.minor == 12
        assert result.patch == 31

    def test_reject_non_year_major(self):
        result = self.parser.parse("1.2.3")
        assert result is None

    def test_reject_invalid_year_range(self):
        result = self.parser.parse("100.1.0")
        assert result is None

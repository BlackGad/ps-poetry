from ps.version import VersionStandard
from ps.version.parsers import CalVerParser


def test_parse_full_year():
    parser = CalVerParser()
    result = parser.parse("2024.1.0")
    assert result is not None
    assert result.major == 2024
    assert result.minor == 1
    assert result.patch == 0
    assert VersionStandard.CALVER in result.standards


def test_parse_short_year():
    parser = CalVerParser()
    result = parser.parse("24.1.0")
    assert result is not None
    assert result.major == 24


def test_parse_date_format():
    parser = CalVerParser()
    result = parser.parse("2024.12.31")
    assert result is not None
    assert result.major == 2024
    assert result.minor == 12
    assert result.patch == 31


def test_reject_non_year_major():
    parser = CalVerParser()
    result = parser.parse("1.2.3")
    assert result is None


def test_reject_invalid_year_range():
    parser = CalVerParser()
    result = parser.parse("100.1.0")
    assert result is None

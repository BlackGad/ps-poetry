from ps.version import VersionStandard
from ps.version.parsers import LooseParser


def test_parse_single_number():
    parser = LooseParser()
    result = parser.parse("1")
    assert result is not None
    assert result.major == 1
    assert result.minor is None
    assert VersionStandard.LOOSE in result.standards


def test_parse_two_numbers():
    parser = LooseParser()
    result = parser.parse("1.2")
    assert result is not None
    assert result.major == 1
    assert result.minor == 2


def test_parse_three_numbers():
    parser = LooseParser()
    result = parser.parse("1.2.3")
    assert result is not None
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_with_suffix():
    parser = LooseParser()
    result = parser.parse("1.2.3-custom")
    assert result is not None
    assert str(result.metadata) == "custom"


def test_reject_invalid():
    parser = LooseParser()
    result = parser.parse("invalid")
    assert result is None

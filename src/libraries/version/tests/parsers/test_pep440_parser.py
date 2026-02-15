from ps.version import VersionStandard
from ps.version.parsers import PEP440Parser


def test_parse_simple_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3")
    assert result is not None
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3
    assert VersionStandard.PEP440 in result.standards


def test_parse_four_part_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3.4")
    assert result is not None
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3
    assert result.rev == 4


def test_parse_alpha_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3a1")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "a"
    assert result.pre.number == 1


def test_parse_beta_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3b2")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "b"
    assert result.pre.number == 2


def test_parse_rc_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3rc1")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "rc"
    assert result.pre.number == 1


def test_parse_post_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3.post1")
    assert result is not None
    assert result.post == 1


def test_parse_dev_version():
    parser = PEP440Parser()
    result = parser.parse("1.2.3.dev1")
    assert result is not None
    assert result.dev == 1


def test_parse_with_metadata():
    parser = PEP440Parser()
    result = parser.parse("1.2.3+g1234567")
    assert result is not None
    assert str(result.metadata) == "g1234567"


def test_parse_complex():
    parser = PEP440Parser()
    result = parser.parse("1.2.3.post4+g1234567.dirty")
    assert result is not None
    assert result.major == 1
    assert result.post == 4
    assert str(result.metadata) == "g1234567.dirty"


def test_reject_semver_format():
    parser = PEP440Parser()
    result = parser.parse("1.2.3-alpha.1")
    assert result is None


def test_reject_invalid():
    parser = PEP440Parser()
    result = parser.parse("invalid")
    assert result is None

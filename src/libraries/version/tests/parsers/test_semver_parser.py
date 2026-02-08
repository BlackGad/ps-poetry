from ps.version import VersionStandard
from ps.version.parsers import SemVerParser


def test_parse_simple_version():
    parser = SemVerParser()
    result = parser.parse("1.2.3")
    assert result is not None
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3
    assert result.standard == VersionStandard.SEMVER


def test_parse_prerelease():
    parser = SemVerParser()
    result = parser.parse("1.2.3-alpha.1")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "alpha"
    assert result.pre.number == 1


def test_parse_with_build():
    parser = SemVerParser()
    result = parser.parse("1.2.3+build.123")
    assert result is not None
    assert str(result.metadata) == "build.123"


def test_parse_full():
    parser = SemVerParser()
    result = parser.parse("1.2.3-rc.1+build.123")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "rc"
    assert result.pre.number == 1
    assert str(result.metadata) == "build.123"


def test_reject_two_part_version():
    parser = SemVerParser()
    result = parser.parse("1.2")
    assert result is None


def test_reject_pep440_format():
    parser = SemVerParser()
    result = parser.parse("1.2.3.post1")
    assert result is None

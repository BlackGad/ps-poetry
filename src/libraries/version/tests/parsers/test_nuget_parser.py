from ps.version.models import VersionStandard
from ps.version.parsers import NuGetParser


def test_parse_three_part_version():
    parser = NuGetParser()
    result = parser.parse("1.2.3")
    assert result is not None
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3
    assert result.standard == VersionStandard.NUGET


def test_parse_four_part_version():
    parser = NuGetParser()
    result = parser.parse("1.2.3.4")
    assert result is not None
    assert result.rev == 4


def test_parse_prerelease():
    parser = NuGetParser()
    result = parser.parse("1.2.3-beta")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "beta"
    assert result.pre.number is None


def test_parse_prerelease_with_number():
    parser = NuGetParser()
    result = parser.parse("1.2.3-beta.1")
    assert result is not None
    assert result.pre is not None
    assert result.pre.name == "beta"
    assert result.pre.number == 1


def test_reject_two_part_version():
    parser = NuGetParser()
    result = parser.parse("1.2")
    assert result is None


def test_reject_with_build_metadata():
    parser = NuGetParser()
    result = parser.parse("1.2.3+build")
    assert result is None

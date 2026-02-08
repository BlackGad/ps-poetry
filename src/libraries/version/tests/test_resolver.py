from ps.version import Version, VersionStandard


def test_parse_empty_string():
    result = Version.parse("")
    assert result.major == 0
    assert result.minor is None
    assert result.patch is None


def test_parse_invalid_version():
    result = Version.parse("invalid")
    assert result.standard == VersionStandard.UNKNOWN


def test_parse_with_whitespace():
    result = Version.parse("  1.2.3  ")
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_zero_version():
    result = Version.parse("0.0.0")
    assert result.major == 0
    assert result.minor == 0
    assert result.patch == 0


def test_parse_pep440_simple():
    result = Version.parse("1.2.3")
    assert result.standard == VersionStandard.PEP440
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_pep440_complex():
    result = Version.parse("1.2.3.post4+g1234567.dirty")
    assert result.standard == VersionStandard.PEP440
    assert result.major == 1
    assert result.post == 4
    assert str(result.metadata) == "g1234567.dirty"


def test_parse_semver_prerelease():
    result = Version.parse("1.2.3-alpha.1")
    assert result.standard == VersionStandard.SEMVER
    assert result.pre is not None
    assert result.pre.name == "alpha"
    assert result.pre.number == 1


def test_parse_nuget_four_part():
    result = Version.parse("1.2.3.4")
    assert result.rev == 4

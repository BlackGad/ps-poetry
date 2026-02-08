from typing import Optional

from ps.version import VersionParser, VersionStandard


def test_parse_empty_string():
    result = VersionParser.parse("")
    assert result.major == 0
    assert result.minor is None
    assert result.patch is None


def test_parse_invalid_version():
    result = VersionParser.parse("invalid")
    assert result.standard == VersionStandard.UNKNOWN


def test_parse_with_whitespace():
    result = VersionParser.parse("  1.2.3  ")
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_zero_version():
    result = VersionParser.parse("0.0.0")
    assert result.major == 0
    assert result.minor == 0
    assert result.patch == 0


def test_parse_pep440_simple():
    result = VersionParser.parse("1.2.3")
    assert result.standard == VersionStandard.PEP440
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_pep440_complex():
    result = VersionParser.parse("1.2.3.post4+g1234567.dirty")
    assert result.standard == VersionStandard.PEP440
    assert result.major == 1
    assert result.post == 4
    assert result.metadata == "g1234567.dirty"


def test_parse_semver_prerelease():
    result = VersionParser.parse("1.2.3-alpha.1")
    assert result.standard == VersionStandard.SEMVER
    assert result.pre is not None
    assert result.pre.name == "alpha"
    assert result.pre.number == 1


def test_parse_nuget_four_part():
    result = VersionParser.parse("1.2.3.4")
    assert result.rev == 4


def test_parse_inputs_first_valid():
    parser = VersionParser([])
    result = parser.parse_inputs(["invalid", "1.2.3"])
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_inputs_with_condition():
    parser = VersionParser([])
    result = parser.parse_inputs(["[in] 1.2.3"])
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_inputs_invalid_condition_skips():
    parser = VersionParser([])
    result = parser.parse_inputs(["[in 1.2.3", "1.2.3"])
    assert result.major == 1
    assert result.minor == 2
    assert result.patch == 3


def test_parse_inputs_fallback():
    parser = VersionParser([])
    result = parser.parse_inputs(["invalid", ""])
    assert result.major == 0
    assert result.minor is None
    assert result.patch is None


def test_materialize_no_resolvers():
    parser = VersionParser([])
    assert parser.materialize("{date:yyyy}") == "{date:yyyy}"


def test_materialize_resolver_order():
    def first_resolver(_args: list[str]) -> Optional[str]:
        return None

    def second_resolver(_args: list[str]) -> Optional[str]:
        return "ok"

    parser = VersionParser([
        ("date", first_resolver),
        ("date", second_resolver),
    ])
    assert parser.materialize("{date:yyyy}") == "ok"


def test_materialize_args_passed():
    def resolver(args: list[str]) -> Optional[str]:
        return ",".join(args)

    parser = VersionParser([("rand", resolver)])
    assert parser.materialize("{rand:num:min..max}") == "num,min..max"


def test_materialize_casts_values():
    def resolver(_args: list[str]) -> Optional[bool]:
        return True

    parser = VersionParser([("flag", resolver)])
    assert parser.materialize("{flag}") == "True"

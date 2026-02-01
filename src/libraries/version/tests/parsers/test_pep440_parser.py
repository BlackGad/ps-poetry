from ps.version.models import VersionStandard
from ps.version.parsers import PEP440Parser


class TestPEP440Parser:
    def setup_method(self):
        self.parser = PEP440Parser()

    def test_parse_simple_version(self):
        result = self.parser.parse("1.2.3")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.standard == VersionStandard.PEP440

    def test_parse_four_part_version(self):
        result = self.parser.parse("1.2.3.4")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.rev == 4

    def test_parse_alpha_version(self):
        result = self.parser.parse("1.2.3a1")
        assert result is not None
        assert result.pre_label == "a"
        assert result.pre_num == 1

    def test_parse_beta_version(self):
        result = self.parser.parse("1.2.3b2")
        assert result is not None
        assert result.pre_label == "b"
        assert result.pre_num == 2

    def test_parse_rc_version(self):
        result = self.parser.parse("1.2.3rc1")
        assert result is not None
        assert result.pre_label == "rc"
        assert result.pre_num == 1

    def test_parse_post_version(self):
        result = self.parser.parse("1.2.3.post1")
        assert result is not None
        assert result.post == 1

    def test_parse_dev_version(self):
        result = self.parser.parse("1.2.3.dev1")
        assert result is not None
        assert result.dev == 1

    def test_parse_with_metadata(self):
        result = self.parser.parse("1.2.3+g1234567")
        assert result is not None
        assert result.meta == "g1234567"

    def test_parse_complex(self):
        result = self.parser.parse("1.2.3.post4+g1234567.dirty")
        assert result is not None
        assert result.major == 1
        assert result.post == 4
        assert result.meta == "g1234567.dirty"

    def test_reject_semver_format(self):
        result = self.parser.parse("1.2.3-alpha.1")
        assert result is None

    def test_reject_invalid(self):
        result = self.parser.parse("invalid")
        assert result is None

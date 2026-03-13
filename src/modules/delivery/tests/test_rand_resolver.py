import re

from ps.plugin.module.delivery.token_resolvers._rand_resolver import RandResolver


def test_rand_no_args_returns_none():
    assert RandResolver()([]) is None


def test_rand_unknown_kind_returns_none():
    assert RandResolver()(["unknown"]) is None


def test_rand_uuid_returns_valid_uuid():
    result = RandResolver()(["uuid"])
    assert isinstance(result, str)
    assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", result)


def test_rand_uuid_values_differ():
    results = {str(RandResolver()(["uuid"])) for _ in range(10)}
    assert len(results) > 1


def test_rand_hash_returns_8_hex_chars():
    result = RandResolver()(["hash"])
    assert isinstance(result, str)
    assert re.fullmatch(r"[0-9a-f]{8}", result)


def test_rand_hash_values_differ():
    results = {str(RandResolver()(["hash"])) for _ in range(10)}
    assert len(results) > 1


def test_rand_num_returns_int():
    result = RandResolver()(["num"])
    assert isinstance(result, int)


def test_rand_num_is_non_negative():
    for _ in range(20):
        result = RandResolver()(["num"])
        assert isinstance(result, int)
        assert result >= 0


def test_rand_num_range_within_bounds():
    for _ in range(50):
        result = RandResolver()(["num", "5..10"])
        assert isinstance(result, int)
        assert 5 <= result <= 10


def test_rand_num_range_single_value():
    result = RandResolver()(["num", "7..7"])
    assert result == 7


def test_rand_num_range_includes_boundaries():
    results = {int(RandResolver()(["num", "0..1"])) for _ in range(50)}  # type: ignore[arg-type]
    assert results == {0, 1}


def test_rand_num_range_invalid_format_returns_none():
    assert RandResolver()(["num", "notarange"]) is None


def test_rand_num_range_non_numeric_returns_none():
    assert RandResolver()(["num", "a..b"]) is None


def test_rand_num_range_inverted_returns_none():
    assert RandResolver()(["num", "10..5"]) is None

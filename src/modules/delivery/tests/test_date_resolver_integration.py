from datetime import UTC, datetime, timedelta, timezone

import pytest

from ps.token_expressions import ExpressionFactory
from ps.plugin.module.delivery.token_resolvers import DateResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_factory(dt: datetime) -> ExpressionFactory:
    return ExpressionFactory([("date", DateResolver(dt))])


# ---------------------------------------------------------------------------
# No-arg token — default ISO date
# ---------------------------------------------------------------------------


def test_factory_date_no_arg_returns_unix_timestamp():
    dt = datetime(2026, 3, 12, 14, 30, 0, tzinfo=UTC)
    assert make_factory(dt).materialize("{date}") == str(int(dt.timestamp()))


def test_factory_date_no_arg_in_longer_string():
    dt = datetime(2026, 3, 12, 8, 0, 0, tzinfo=UTC)
    assert make_factory(dt).materialize("ts={date}") == f"ts={int(dt.timestamp())}"


# ---------------------------------------------------------------------------
# C#-style format tokens — colon splitting by factory
# ---------------------------------------------------------------------------


def test_factory_date_cs_date_format():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:yyyy.MM.dd}") == "2026.03.12"


def test_factory_date_cs_compact_date():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:yyyyMMdd}") == "20260312"


def test_factory_date_cs_short_year():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:yy.MM.dd}") == "26.03.12"


def test_factory_date_cs_time_format_split_by_factory():
    # Factory splits on ':' so {date:HH:mm:ss} -> args=["HH", "mm", "ss"]
    dt = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:HH:mm:ss}") == "14:05:09"


def test_factory_date_cs_datetime_with_time_split():
    dt = datetime(2026, 3, 12, 8, 30, 45, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:yyyy-MM-dd HH:mm:ss}") == "2026-03-12 08:30:45"


def test_factory_date_cs_time_hours_minutes_split():
    dt = datetime(2026, 3, 12, 8, 30, 0, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:HH:mm}") == "08:30"


# ---------------------------------------------------------------------------
# Python strftime tokens
# ---------------------------------------------------------------------------


def test_factory_date_python_strftime_date():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:%Y-%m-%d}") == "2026-03-12"


def test_factory_date_python_strftime_time_split():
    dt = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:%H:%M:%S}") == "14:05:09"


def test_factory_date_mixed_cs_and_python_tokens():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:yyyy-%m-dd}") == "2026-03-12"


# ---------------------------------------------------------------------------
# Named standard formats — no colon in format name, single arg
# ---------------------------------------------------------------------------


def test_factory_date_standard_sortable():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:sortable}") == "2026-03-12T16:05:09"


def test_factory_date_standard_sortable_alias_s():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:s}") == "2026-03-12T16:05:09"


def test_factory_date_standard_universal():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:universal}") == "2026-03-12 16:05:09Z"


def test_factory_date_standard_universal_alias_u():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:u}") == "2026-03-12 16:05:09Z"


def test_factory_date_standard_universal_converts_to_utc():
    dt = datetime(2026, 3, 12, 18, 5, 9, tzinfo=timezone(timedelta(hours=2)))
    assert make_factory(dt).materialize("{date:universal}") == "2026-03-12 16:05:09Z"


def test_factory_date_standard_iso():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:iso}") == "2026-03-12T16:05:09+00:00"


def test_factory_date_standard_iso_round():
    dt = datetime(2026, 3, 12, 16, 5, 9, 123456, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:iso-round}") == "2026-03-12T16:05:09.123456+00:00"


def test_factory_date_standard_iso_round_alias_o_lowercase():
    dt = datetime(2026, 3, 12, 16, 5, 9, 123456, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:o}") == "2026-03-12T16:05:09.123456+00:00"


def test_factory_date_standard_iso_round_alias_o_uppercase():
    dt = datetime(2026, 3, 12, 16, 5, 9, 123456, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:O}") == "2026-03-12T16:05:09.123456+00:00"


# ---------------------------------------------------------------------------
# Embedding in larger templates
# ---------------------------------------------------------------------------


def test_factory_date_embedded_in_version_string():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("1.0.0+{date:yyyyMMdd}") == "1.0.0+20260312"


def test_factory_date_multiple_tokens_in_template():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:yyyy}-{date:MM}-{date:dd}") == "2026-03-12"


@pytest.mark.parametrize(("template", "expected"), [
    ("{date:yyyy}", "2026"),
    ("{date:MM}", "03"),
    ("{date:dd}", "12"),
    ("{date:HH}", "14"),
    ("{date:mm}", "05"),
    ("{date:ss}", "09"),
    ("{date:yy}", "26"),
])
def test_factory_date_individual_cs_tokens(template: str, expected: str):
    dt = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    assert make_factory(dt).materialize(template) == expected


# ---------------------------------------------------------------------------
# Numeric formats via factory — unix, ticks
# ---------------------------------------------------------------------------


def test_factory_date_unix_returns_int_as_string_in_template():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    result = make_factory(dt).materialize("{date:unix}")
    assert result == str(int(dt.timestamp()))


def test_factory_date_unix_embedded_in_template():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    result = make_factory(dt).materialize("ts={date:unix}")
    assert result == f"ts={int(dt.timestamp())}"


def test_factory_date_ticks_returns_int_as_string_in_template():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    expected = str(int((dt.timestamp() + 62135596800) * 10_000_000))
    result = make_factory(dt).materialize("{date:ticks}")
    assert result == expected


def test_factory_date_ticks_dotnet_epoch_is_zero():
    dt = datetime(1, 1, 1, tzinfo=UTC)
    assert make_factory(dt).materialize("{date:ticks}") == "0"


# ---------------------------------------------------------------------------
# Comparison via factory.match — uses unix (int) default for > / < operators
# ---------------------------------------------------------------------------


def test_factory_date_match_greater_than_past_date():
    dt = datetime(2026, 3, 12, 12, 0, 0, tzinfo=UTC)
    past = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    assert make_factory(dt).match(f"{{date}} > {past}") is True


def test_factory_date_match_less_than_future_date():
    dt = datetime(2026, 3, 12, 12, 0, 0, tzinfo=UTC)
    future = int(datetime(2027, 1, 1, tzinfo=UTC).timestamp())
    assert make_factory(dt).match(f"{{date}} < {future}") is True


def test_factory_date_match_not_greater_than_future_date():
    dt = datetime(2026, 3, 12, 12, 0, 0, tzinfo=UTC)
    future = int(datetime(2027, 1, 1, tzinfo=UTC).timestamp())
    assert make_factory(dt).match(f"{{date}} > {future}") is False


def test_factory_date_match_not_less_than_past_date():
    dt = datetime(2026, 3, 12, 12, 0, 0, tzinfo=UTC)
    past = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    assert make_factory(dt).match(f"{{date}} < {past}") is False


def test_factory_date_match_in_range():
    dt = datetime(2026, 3, 12, 12, 0, 0, tzinfo=UTC)
    past = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    future = int(datetime(2027, 1, 1, tzinfo=UTC).timestamp())
    assert make_factory(dt).match(f"{{date}} > {past} and {{date}} < {future}") is True


def test_factory_date_match_outside_range():
    dt = datetime(2025, 6, 1, 0, 0, 0, tzinfo=UTC)
    past = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    future = int(datetime(2027, 1, 1, tzinfo=UTC).timestamp())
    assert make_factory(dt).match(f"{{date}} > {past} and {{date}} < {future}") is False


def test_factory_date_match_two_dates_ordering():
    dt_earlier = datetime(2026, 1, 1, tzinfo=UTC)
    dt_later = datetime(2026, 12, 31, tzinfo=UTC)
    earlier_ts = int(dt_earlier.timestamp())
    factory_later = make_factory(dt_later)
    assert factory_later.match(f"{{date}} > {earlier_ts}") is True


# ---------------------------------------------------------------------------
# from: format — parsing date strings into unix timestamps
# ---------------------------------------------------------------------------


def test_factory_date_from_sortable():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = str(int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp()))
    assert make_factory(dt).materialize("{date:from:2026-03-12T16:05:09}") == expected


def test_factory_date_from_universal_with_z():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = str(int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp()))
    assert make_factory(dt).materialize("{date:from:2026-03-12 16:05:09Z}") == expected


def test_factory_date_from_datetime_without_seconds():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = str(int(datetime(2026, 3, 12, 8, 30, tzinfo=UTC).timestamp()))
    assert make_factory(dt).materialize("{date:from:2026-03-12 08:30}") == expected


def test_factory_date_from_date_only():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = str(int(datetime(2026, 3, 12, tzinfo=UTC).timestamp()))
    assert make_factory(dt).materialize("{date:from:2026-03-12}") == expected


def test_factory_date_from_unix_string():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    ts = int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp())
    assert make_factory(dt).materialize(f"{{date:from:{ts}}}") == str(ts)


# ---------------------------------------------------------------------------
# from: format — comparison via factory.match (the main use case)
# ---------------------------------------------------------------------------


def test_factory_date_match_gt_from_sortable():
    dt = datetime(2026, 3, 12, 12, 0, 0, tzinfo=UTC)
    assert make_factory(dt).match("{date} > {date:from:2026-03-12 08:30}") is True


def test_factory_date_match_lt_from_sortable():
    dt = datetime(2026, 3, 12, 7, 0, 0, tzinfo=UTC)
    assert make_factory(dt).match("{date} < {date:from:2026-03-12 08:30}") is True


def test_factory_date_match_not_gt_from_future():
    dt = datetime(2026, 3, 12, 7, 0, 0, tzinfo=UTC)
    assert make_factory(dt).match("{date} > {date:from:2026-03-12 08:30}") is False


def test_factory_date_match_in_range_from_strings():
    dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
    assert make_factory(dt).match(
        "{date} > {date:from:2026-01-01} and {date} < {date:from:2027-01-01}"
    ) is True


def test_factory_date_match_outside_range_from_strings():
    dt = datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC)
    assert make_factory(dt).match(
        "{date} > {date:from:2026-01-01} and {date} < {date:from:2027-01-01}"
    ) is False

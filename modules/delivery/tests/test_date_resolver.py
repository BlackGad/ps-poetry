from datetime import UTC, datetime, timedelta, timezone

import pytest

from ps.plugin.module.delivery.token_resolvers._date_resolver import DateResolver


# ---------------------------------------------------------------------------
# DateResolver.__call__ — no args (default ISO date)
# ---------------------------------------------------------------------------


def test_date_resolver_no_args_returns_unix_timestamp():
    dt = datetime(2026, 3, 12, 14, 30, 0, tzinfo=UTC)
    resolver = DateResolver(dt)
    assert resolver([]) == int(dt.timestamp())


def test_date_resolver_no_args_returns_int():
    dt = datetime(2026, 3, 12, 23, 59, 59, tzinfo=UTC)
    resolver = DateResolver(dt)
    assert isinstance(resolver([]), int)


# ---------------------------------------------------------------------------
# DateResolver.__call__ — C#-style format tokens
# ---------------------------------------------------------------------------


def test_date_resolver_cs_full_date():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["yyyy.MM.dd"]) == "2026.03.12"


def test_date_resolver_cs_short_year():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["yy.MM.dd"]) == "26.03.12"


def test_date_resolver_cs_no_separator():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["yyyyMMdd"]) == "20260312"


def test_date_resolver_cs_time_components():
    dt = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["HH", "mm", "ss"]) == "14:05:09"


def test_date_resolver_cs_combined_datetime():
    dt = datetime(2026, 3, 12, 8, 30, 0, tzinfo=UTC)
    assert DateResolver(dt)(["yyyy-MM-dd HH", "mm"]) == "2026-03-12 08:30"


def test_date_resolver_cs_yyyy_does_not_shadow_yy():
    dt = datetime(2026, 1, 1, tzinfo=UTC)
    assert DateResolver(dt)(["yyyy"]) == "2026"
    assert DateResolver(dt)(["yy"]) == "26"


# ---------------------------------------------------------------------------
# DateResolver.__call__ — Python strftime tokens
# ---------------------------------------------------------------------------


def test_date_resolver_python_strftime_year_month():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["%Y %m"]) == "2026 03"


def test_date_resolver_python_strftime_date():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["%Y-%m-%d"]) == "2026-03-12"


def test_date_resolver_python_strftime_preserved_over_cs():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["%Y-%m-%d"]) == DateResolver(dt)(["yyyy-MM-dd"])


def test_date_resolver_mixed_python_and_cs_tokens():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["yyyy-%m-dd"]) == "2026-03-12"


# ---------------------------------------------------------------------------
# DateResolver.__call__ — standard named formats
# ---------------------------------------------------------------------------


def test_date_resolver_standard_sortable():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["sortable"]) == "2026-03-12T16:05:09"


def test_date_resolver_standard_sortable_alias_s():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["s"]) == "2026-03-12T16:05:09"


def test_date_resolver_standard_universal_utc():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["universal"]) == "2026-03-12 16:05:09Z"


def test_date_resolver_standard_universal_converts_to_utc():
    dt = datetime(2026, 3, 12, 18, 5, 9, tzinfo=timezone(timedelta(hours=2)))
    assert DateResolver(dt)(["universal"]) == "2026-03-12 16:05:09Z"


def test_date_resolver_standard_universal_alias_u():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["u"]) == DateResolver(dt)(["universal"])


def test_date_resolver_standard_iso():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["iso"]) == "2026-03-12T16:05:09+00:00"


def test_date_resolver_standard_iso_round():
    dt = datetime(2026, 3, 12, 16, 5, 9, 123456, tzinfo=UTC)
    assert DateResolver(dt)(["iso-round"]) == "2026-03-12T16:05:09.123456+00:00"


def test_date_resolver_standard_iso_round_alias_o_lowercase():
    dt = datetime(2026, 3, 12, 16, 5, 9, 123456, tzinfo=UTC)
    assert DateResolver(dt)(["o"]) == DateResolver(dt)(["iso-round"])


def test_date_resolver_standard_iso_round_alias_o_uppercase():
    dt = datetime(2026, 3, 12, 16, 5, 9, 123456, tzinfo=UTC)
    assert DateResolver(dt)(["O"]) == DateResolver(dt)(["iso-round"])


def test_date_resolver_standard_universal_naive_datetime():
    dt = datetime(2026, 3, 12, 16, 5, 9)  # noqa: DTZ001
    assert DateResolver(dt)(["universal"]) == "2026-03-12 16:05:09Z"


# ---------------------------------------------------------------------------
# DateResolver — captures datetime at construction time
# ---------------------------------------------------------------------------


def test_date_resolver_captures_dt_at_construction():
    dt1 = datetime(2026, 3, 12, tzinfo=UTC)
    dt2 = datetime(2099, 1, 1, tzinfo=UTC)
    r1 = DateResolver(dt1)
    r2 = DateResolver(dt2)
    assert r1(["yyyy"]) == "2026"
    assert r2(["yyyy"]) == "2099"


# ---------------------------------------------------------------------------
# DateResolver — is a BaseResolver
# ---------------------------------------------------------------------------


def test_date_resolver_is_callable():
    resolver = DateResolver(datetime(2026, 3, 12, tzinfo=UTC))
    assert callable(resolver)


def test_date_resolver_extra_args_rejoined_by_colon():
    # Extra args are rejoined: ["yyyy", "MM"] → "yyyy:MM" which has no C# meaning
    # but demonstrates that args are concatenated with ':'
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert DateResolver(dt)(["yyyy", "MM"]) == "2026:03"


@pytest.mark.parametrize(("fmt", "expected"), [
    ("yyyy", "2026"),
    ("MM", "03"),
    ("dd", "12"),
    ("HH", "14"),
    ("mm", "05"),
    ("ss", "09"),
    ("yy", "26"),
])
def test_date_resolver_individual_cs_tokens(fmt: str, expected: str):
    dt = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)([fmt]) == expected


# ---------------------------------------------------------------------------
# DateResolver.__call__ — numeric formats (unix, ticks)
# ---------------------------------------------------------------------------


def test_date_resolver_unix_returns_int():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    result = DateResolver(dt)(["unix"])
    assert isinstance(result, int)


def test_date_resolver_unix_value():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt)(["unix"]) == int(dt.timestamp())


def test_date_resolver_unix_converts_offset_aware_to_utc():
    dt_offset = datetime(2026, 3, 12, 18, 5, 9, tzinfo=timezone(timedelta(hours=2)))
    dt_utc = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    assert DateResolver(dt_offset)(["unix"]) == DateResolver(dt_utc)(["unix"])


def test_date_resolver_ticks_returns_int():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    result = DateResolver(dt)(["ticks"])
    assert isinstance(result, int)


def test_date_resolver_ticks_value():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    expected = int((dt.timestamp() + 62135596800) * 10_000_000)
    assert DateResolver(dt)(["ticks"]) == expected


def test_date_resolver_ticks_dotnet_epoch_is_zero():
    # datetime(1, 1, 1, tzinfo=UTC) is the .NET epoch — ticks should be 0
    dt = datetime(1, 1, 1, tzinfo=UTC)
    assert DateResolver(dt)(["ticks"]) == 0


def test_date_resolver_ticks_unix_epoch_is_known_constant():
    # .NET ticks at Unix epoch = 621355968000000000
    dt = datetime(1970, 1, 1, tzinfo=UTC)
    assert DateResolver(dt)(["ticks"]) == 621355968000000000


def test_date_resolver_ticks_greater_than_unix():
    dt = datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC)
    ticks = DateResolver(dt)(["ticks"])
    unix = DateResolver(dt)(["unix"])
    assert isinstance(ticks, int)
    assert isinstance(unix, int)
    assert ticks > unix


# ---------------------------------------------------------------------------
# DateResolver.__call__ — from: parsing format
# ---------------------------------------------------------------------------


def test_date_resolver_from_returns_int():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    result = DateResolver(dt)(["from", "2026-03-12"])
    assert isinstance(result, int)


def test_date_resolver_from_sortable():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12T16", "05", "09"]) == expected


def test_date_resolver_from_sortable_without_seconds():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, 16, 5, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12T16", "05"]) == expected


def test_date_resolver_from_universal_with_z():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12 16", "05", "09Z"]) == expected


def test_date_resolver_from_universal_without_z():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12 16", "05", "09"]) == expected


def test_date_resolver_from_datetime_with_space_and_minutes():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, 8, 30, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12 08", "30"]) == expected


def test_date_resolver_from_date_only():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12"]) == expected


def test_date_resolver_from_iso_with_offset():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", "2026-03-12T16", "05", "09+00", "00"]) == expected


def test_date_resolver_from_unix_timestamp_string():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    ts = int(datetime(2026, 3, 12, 16, 5, 9, tzinfo=UTC).timestamp())
    assert DateResolver(dt)(["from", str(ts)]) == ts


def test_date_resolver_from_ignores_resolver_dt():
    dt1 = datetime(2026, 1, 1, tzinfo=UTC)
    dt2 = datetime(2099, 1, 1, tzinfo=UTC)
    expected = int(datetime(2026, 3, 12, tzinfo=UTC).timestamp())
    assert DateResolver(dt1)(["from", "2026-03-12"]) == expected
    assert DateResolver(dt2)(["from", "2026-03-12"]) == expected

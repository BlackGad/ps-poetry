from datetime import UTC, datetime
from typing import Optional

from ps.token_expressions import BaseResolver
from ps.token_expressions.token_resolvers._base_resolver import TokenValue

_CS_TO_PY_TOKENS: list[tuple[str, str]] = [
    ("yyyy", "%Y"),
    ("yy", "%y"),
    ("MM", "%m"),
    ("dd", "%d"),
    ("HH", "%H"),
    ("mm", "%M"),
    ("ss", "%S"),
]

_STANDARD_FORMATS: dict[str, str] = {
    "iso": "iso",
    "iso-round": "iso-round",
    "sortable": "sortable",
    "universal": "universal",
    "unix": "unix",
    "ticks": "ticks",
    "o": "iso-round",
    "O": "iso-round",
    "s": "sortable",
    "u": "universal",
}

# Seconds between .NET epoch (0001-01-01) and Unix epoch (1970-01-01)
_UNIX_TO_DOTNET_EPOCH_SECONDS: int = 62135596800

_PARSE_FORMATS: list[str] = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]


class DateResolver(BaseResolver):
    def __init__(self, dt: datetime) -> None:
        self._dt = dt

    def __call__(self, args: list[str]) -> Optional[TokenValue]:
        if not args:
            return format_date(self._dt, "unix")
        return format_date(self._dt, ":".join(args))


def format_date(dt: datetime, fmt: str) -> TokenValue:
    if fmt.startswith("from:"):
        return _parse_date(fmt[5:])
    standard = _STANDARD_FORMATS.get(fmt)
    if standard is not None:
        return _format_standard_date(dt, standard)
    py_format = _translate_datetime_format(fmt)
    return dt.strftime(py_format)


def _translate_datetime_format(fmt: str) -> str:
    parts: list[str] = []
    i = 0
    length = len(fmt)

    while i < length:
        ch = fmt[i]

        if ch == "%":
            if i + 1 < length:
                parts.append(fmt[i:i + 2])
                i += 2
            else:
                parts.append("%")
                i += 1
            continue

        for cs_token, py_token in _CS_TO_PY_TOKENS:
            if fmt.startswith(cs_token, i):
                parts.append(py_token)
                i += len(cs_token)
                break
        else:
            parts.append(ch)
            i += 1

    return "".join(parts)


def _format_standard_date(dt: datetime, standard: str) -> TokenValue:
    if standard == "unix":
        return int(dt.timestamp())

    if standard == "ticks":
        return int((dt.timestamp() + _UNIX_TO_DOTNET_EPOCH_SECONDS) * 10_000_000)

    if standard == "sortable":
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    if standard == "universal":
        utc_dt = dt if dt.tzinfo is None else dt.astimezone(UTC)
        return utc_dt.strftime("%Y-%m-%d %H:%M:%SZ")

    if standard == "iso":
        return dt.isoformat(timespec="seconds")

    if standard == "iso-round":
        return dt.isoformat(timespec="microseconds")

    raise ValueError(f"Unsupported datetime format standard: {standard}")


def _parse_date(value: str) -> int:
    try:
        return int(float(value))
    except ValueError:
        pass

    for fmt in _PARSE_FORMATS:
        try:
            return int(datetime.strptime(value, fmt).replace(tzinfo=UTC).timestamp())
        except ValueError:
            continue

    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return int(dt.timestamp())
    except ValueError:
        pass

    raise ValueError(f"Cannot parse date: {value!r}")

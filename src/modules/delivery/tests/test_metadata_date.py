from datetime import datetime, UTC
from unittest.mock import patch

from ps.version import Version

from ps.plugin.module.delivery.stages._metadata import _format_date

from .conftest import make_io, make_project, resolve
from ps.plugin.module.delivery.stages._metadata import resolve_environment_metadata


# ---------------------------------------------------------------------------
# _format_date helper
# ---------------------------------------------------------------------------


def test_format_date_full_date():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert _format_date(dt, "yyyy.MM.dd") == "2026.03.12"


def test_format_date_short_year():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert _format_date(dt, "yy.MM.dd") == "26.03.12"


def test_format_date_no_separator():
    dt = datetime(2026, 3, 12, tzinfo=UTC)
    assert _format_date(dt, "yyyyMMdd") == "20260312"


def test_format_date_time_components():
    dt = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    assert _format_date(dt, "HH:mm:ss") == "14:05:09"


def test_format_date_combined():
    dt = datetime(2026, 3, 12, 8, 30, 0, tzinfo=UTC)
    assert _format_date(dt, "yyyy-MM-dd HH:mm") == "2026-03-12 08:30"


def test_format_date_yyyy_does_not_shadow_yy():
    dt = datetime(2026, 1, 1, tzinfo=UTC)
    assert _format_date(dt, "yyyy") == "2026"
    assert _format_date(dt, "yy") == "26"


# ---------------------------------------------------------------------------
# date provider in patterns
# ---------------------------------------------------------------------------


def test_date_with_format_produces_version(tmp_path):
    fixed_now = datetime(2026, 3, 12, tzinfo=UTC)
    with patch("ps.plugin.module.delivery.stages._metadata.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_now
        result = resolve(tmp_path, project_patterns=["1.{date:yyyyMMdd}.0"])
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("1.20260312.0")


def test_date_calver_format(tmp_path):
    fixed_now = datetime(2026, 3, 12, tzinfo=UTC)
    with patch("ps.plugin.module.delivery.stages._metadata.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_now
        result = resolve(tmp_path, project_patterns=["{date:yyyy}.{date:MM}.{date:dd}"])
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("2026.3.12")


def test_date_with_time_components(tmp_path):
    fixed_now = datetime(2026, 3, 12, 14, 5, 9, tzinfo=UTC)
    with patch("ps.plugin.module.delivery.stages._metadata.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_now
        result = resolve(tmp_path, project_patterns=["1.0.{date:HHmmss}"])
    versions = list(result.projects.values())
    assert versions[0].version == Version.parse("1.0.140509")


def test_date_now_shared_across_projects(tmp_path):
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    proj_a_dir = tmp_path / "proj_a"
    proj_a_dir.mkdir()
    proj_b_dir = tmp_path / "proj_b"
    proj_b_dir.mkdir()

    host = make_project(host_dir, name="host", version="0.0.0")
    proj_a = make_project(proj_a_dir, name="proj-a", version="0.0.1", patterns=["1.{date:yyyyMMdd}.0"])
    proj_b = make_project(proj_b_dir, name="proj-b", version="0.0.2", patterns=["1.{date:yyyyMMdd}.0"])

    assert host is not None
    assert proj_a is not None
    assert proj_b is not None

    fixed = datetime(2026, 3, 12, tzinfo=UTC)
    with patch("ps.plugin.module.delivery.stages._metadata.datetime") as mock_dt:
        mock_dt.now.return_value = fixed
        result = resolve_environment_metadata(make_io(), None, host, [proj_a, proj_b])

    versions = list(result.projects.values())
    assert len(versions) == 2
    assert all(v.version == Version.parse("1.20260312.0") for v in versions)

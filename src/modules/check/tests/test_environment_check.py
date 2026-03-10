from pathlib import Path
from unittest.mock import MagicMock
from cleo.io.io import IO

from ps.plugin.sdk.project import (
    Project,
    parse_project,
)
from ps.plugin.module.check.checks.environment_check import EnvironmentCheck


def make_project(tmp_path: Path, name: str, sources: str = "") -> Project:
    pyproject = tmp_path / name / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        f"""
[project]
name = "{name}"
version = "1.0.0"
{sources}
""",
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    return project


def make_io():
    return MagicMock(spec=IO)


# --- no conflicts ---

def test_no_projects_returns_none():
    check = EnvironmentCheck()
    result = check.check(make_io(), [], fix=False)
    assert result is None


def test_single_project_no_sources_returns_none(tmp_path):
    project = make_project(tmp_path, "proj-a")
    result = EnvironmentCheck().check(make_io(), [project], fix=False)
    assert result is None


def test_single_project_with_sources_returns_none(tmp_path):
    project = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "my-index"
url = "https://example.com/simple/"
priority = "primary"
""")
    result = EnvironmentCheck().check(make_io(), [project], fix=False)
    assert result is None


def test_same_source_same_url_and_priority_returns_none(tmp_path):
    source_block = """
[[tool.poetry.source]]
name = "shared"
url = "https://example.com/simple/"
priority = "primary"
"""
    proj_a = make_project(tmp_path, "proj-a", sources=source_block)
    proj_b = make_project(tmp_path, "proj-b", sources=source_block)
    result = EnvironmentCheck().check(make_io(), [proj_a, proj_b], fix=False)
    assert result is None


def test_same_source_name_different_case_same_values_returns_none(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "My-Index"
url = "https://example.com/simple/"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "my-index"
url = "https://example.com/simple/"
""")
    result = EnvironmentCheck().check(make_io(), [proj_a, proj_b], fix=False)
    assert result is None


# --- url conflicts ---

def test_conflicting_urls_returns_exception(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://a.example.com/simple/"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://b.example.com/simple/"
""")
    io = make_io()
    result = EnvironmentCheck().check(io, [proj_a, proj_b], fix=False)
    assert result is not None
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "conflicting urls" in written


def test_conflicting_urls_message_contains_all_urls(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://a.example.com/"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://b.example.com/"
""")
    io = make_io()
    EnvironmentCheck().check(io, [proj_a, proj_b], fix=False)

    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "https://a.example.com/" in written
    assert "https://b.example.com/" in written
    assert "proj-a" in written
    assert "proj-b" in written


def test_same_url_shared_by_multiple_projects_grouped_on_one_line(tmp_path):
    source_block = """
[[tool.poetry.source]]
name = "shared"
url = "https://a.example.com/"
"""
    proj_a = make_project(tmp_path, "proj-a", sources=source_block)
    proj_b = make_project(tmp_path, "proj-b", sources=source_block)
    proj_c = make_project(tmp_path, "proj-c", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://b.example.com/"
""")
    io = make_io()
    EnvironmentCheck().check(io, [proj_a, proj_b, proj_c], fix=False)

    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    # proj-a and proj-b share the same url → must appear on the same line
    for line in written.splitlines():
        if "https://a.example.com/" in line:
            assert "proj-a" in line
            assert "proj-b" in line
            break
    else:
        raise AssertionError("Expected line with https://a.example.com/ not found")


# --- priority conflicts ---

def test_conflicting_priorities_returns_exception(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://example.com/"
priority = "primary"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://example.com/"
priority = "secondary"
""")
    io = make_io()
    result = EnvironmentCheck().check(io, [proj_a, proj_b], fix=False)
    assert result is not None
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "conflicting priorities" in written


def test_conflicting_priorities_message_contains_all_values(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://example.com/"
priority = "primary"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://example.com/"
priority = "secondary"
""")
    io = make_io()
    EnvironmentCheck().check(io, [proj_a, proj_b], fix=False)

    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "primary" in written
    assert "secondary" in written


# --- both conflicts ---

def test_both_url_and_priority_conflict_reports_two_errors(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://a.example.com/"
priority = "primary"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "shared"
url = "https://b.example.com/"
priority = "secondary"
""")
    io = make_io()
    result = EnvironmentCheck().check(io, [proj_a, proj_b], fix=False)

    assert result is not None
    assert "2 error(s)" in str(result)
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "conflicting urls" in written
    assert "conflicting priorities" in written


# --- unrelated sources ---

def test_different_source_names_no_conflict(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", sources="""
[[tool.poetry.source]]
name = "index-a"
url = "https://a.example.com/"
""")
    proj_b = make_project(tmp_path, "proj-b", sources="""
[[tool.poetry.source]]
name = "index-b"
url = "https://b.example.com/"
""")
    result = EnvironmentCheck().check(make_io(), [proj_a, proj_b], fix=False)
    assert result is None

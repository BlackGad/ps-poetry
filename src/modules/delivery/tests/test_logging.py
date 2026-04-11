from pathlib import Path
from unittest.mock import MagicMock

from cleo.io.io import IO

from ps.version import Version
from ps.plugin.sdk.project import Environment

from ps.plugin.module.delivery.stages._metadata import (
    DeliverableType,
    ResolvedEnvironmentMetadata,
    ResolvedProjectMetadata,
)
from ps.plugin.module.delivery.stages._logging import (
    build_dependency_tree,
    build_publish_waves,
    log_dependency_tree,
    log_publish_waves,
)


def _make_io() -> MagicMock:
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False
    return io


def _make_project(tmp_path: Path, name: str, deps: str = "") -> Path:
    proj_dir = tmp_path / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    pyproject = proj_dir / "pyproject.toml"
    pyproject.write_text(
        f'[project]\nname = "{name}"\nversion = "1.0.0"\n\n'
        f"[tool.poetry.dependencies]\n"
        f'python = "^3.10"\n{deps}',
        encoding="utf-8",
    )
    return pyproject


def _setup_env(tmp_path: Path, project_names: list[str], deps: dict[str, str] | None = None) -> tuple[Environment, ResolvedEnvironmentMetadata, list]:
    deps = deps or {}
    host_path = _make_project(tmp_path, "host")
    env = Environment(host_path)

    metadata = ResolvedEnvironmentMetadata()
    added_projects = []
    for name in project_names:
        dep_str = deps.get(name, "")
        proj_path = _make_project(tmp_path, name, dep_str)
        env.add_project(proj_path)
        resolved_path = proj_path.resolve()
        metadata.projects[resolved_path] = ResolvedProjectMetadata(
            version=Version.parse("1.0.0") or Version(),
            deliver=DeliverableType.ENABLED,
        )
        added_projects.append(env._projects[proj_path.resolve()])

    return env, metadata, added_projects


# ---------------------------------------------------------------------------
# build_dependency_tree
# ---------------------------------------------------------------------------

def test_build_dependency_tree_no_projects(tmp_path):
    host_path = _make_project(tmp_path, "host")
    env = Environment(host_path)
    metadata = ResolvedEnvironmentMetadata()
    result = build_dependency_tree([], env, metadata)
    assert result == []


def test_build_dependency_tree_single_project(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a"])
    result = build_dependency_tree(projects, env, metadata)
    assert len(result) == 1
    assert result[0].name == "lib-a"
    assert result[0].version == "1.0.0"
    assert result[0].children == []


def test_build_dependency_tree_independent_projects(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a", "lib-b"])
    result = build_dependency_tree(projects, env, metadata)
    assert len(result) == 2
    names = {n.name for n in result}
    assert names == {"lib-a", "lib-b"}


# ---------------------------------------------------------------------------
# build_publish_waves
# ---------------------------------------------------------------------------

def test_build_publish_waves_no_projects(tmp_path):
    host_path = _make_project(tmp_path, "host")
    env = Environment(host_path)
    metadata = ResolvedEnvironmentMetadata()
    result = build_publish_waves([], env, metadata)
    assert result == []


def test_build_publish_waves_single_project(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a"])
    result = build_publish_waves(projects, env, metadata)
    assert len(result) == 1
    assert result[0].index == 1
    assert len(result[0].projects) == 1
    assert result[0].projects[0].name == "lib-a"


def test_build_publish_waves_independent_same_wave(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a", "lib-b"])
    result = build_publish_waves(projects, env, metadata)
    assert len(result) == 1
    names = {p.name for p in result[0].projects}
    assert names == {"lib-a", "lib-b"}


# ---------------------------------------------------------------------------
# log_dependency_tree / log_publish_waves
# ---------------------------------------------------------------------------

def test_log_dependency_tree_writes_output(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a"])
    io = _make_io()
    log_dependency_tree(io, projects, env, metadata)
    assert io.write_line.call_count > 0
    lines = [call.args[0] for call in io.write_line.call_args_list]
    assert any("Dependency tree" in line for line in lines)
    assert any("lib-a" in line for line in lines)


def test_log_publish_waves_writes_output(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a"])
    io = _make_io()
    log_publish_waves(io, projects, env, metadata)
    assert io.write_line.call_count > 0
    lines = [call.args[0] for call in io.write_line.call_args_list]
    assert any("Publish order" in line for line in lines)


def test_log_dependency_tree_custom_title(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a"])
    io = _make_io()
    log_dependency_tree(io, projects, env, metadata, title="My tree")
    lines = [call.args[0] for call in io.write_line.call_args_list]
    assert any("My tree" in line for line in lines)


def test_log_publish_waves_custom_title(tmp_path):
    env, metadata, projects = _setup_env(tmp_path, ["lib-a"])
    io = _make_io()
    log_publish_waves(io, projects, env, metadata, title="Custom waves")
    lines = [call.args[0] for call in io.write_line.call_args_list]
    assert any("Custom waves" in line for line in lines)

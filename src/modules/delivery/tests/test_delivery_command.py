import json
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

from cleo.io.io import IO

from ps.di import DI
from ps.plugin.sdk.project import Environment

from ps.plugin.module.delivery.commands._delivery_command import DeliveryCommand
from ps.plugin.module.delivery.output._models import ProjectResolution
from ps.plugin.module.delivery.stages._metadata import (
    DeliverableType,
    ResolvedEnvironmentMetadata,
    ResolvedProjectMetadata,
)
from ps.version import Version


def _make_project_file(tmp_path: Path, name: str) -> Path:
    proj_dir = tmp_path / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    pyproject = proj_dir / "pyproject.toml"
    pyproject.write_text(
        f'[project]\nname = "{name}"\nversion = "1.0.0"\n\n'
        f'[tool.poetry.dependencies]\npython = "^3.10"\n',
        encoding="utf-8",
    )
    return pyproject


def _setup(tmp_path: Path, project_names: list[str]) -> tuple[DI, Environment, ResolvedEnvironmentMetadata]:
    host_path = _make_project_file(tmp_path, "host")
    env = Environment(host_path)
    metadata = ResolvedEnvironmentMetadata()
    host_resolved = host_path.resolve()
    metadata.projects[host_resolved] = ResolvedProjectMetadata(
        version=Version.parse("1.0.0") or Version(),
        deliver=DeliverableType.ENABLED,
    )
    for name in project_names:
        proj_path = _make_project_file(tmp_path, name)
        env.add_project(proj_path)
        resolved = proj_path.resolve()
        metadata.projects[resolved] = ResolvedProjectMetadata(
            version=Version.parse("1.0.0") or Version(),
            deliver=DeliverableType.ENABLED,
        )
        metadata.resolutions.append(
            ProjectResolution(name=name, path=str(resolved), version="1.0.0", deliver="Enabled")
        )

    di = DI()
    di.register(Environment).factory(lambda: env)

    return di, env, metadata


def _make_command(di: DI, metadata: ResolvedEnvironmentMetadata, options: dict[str, bool] | None = None) -> tuple[DeliveryCommand, MagicMock]:
    options = options or {}
    cmd = DeliveryCommand(di)
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = False
    io.is_debug.return_value = False

    type(cmd).io = PropertyMock(return_value=io)
    cmd.option = MagicMock(side_effect=lambda name: options.get(name, False))

    di.satisfy = MagicMock(return_value=lambda: metadata)

    return cmd, io


# ---------------------------------------------------------------------------
# handle — no filter flags → all sections rendered
# ---------------------------------------------------------------------------

def test_handle_no_flags_renders_all_sections(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    cmd, io = _make_command(di, metadata)
    result = cmd.handle()
    assert result == 0
    lines = [c.args[0] for c in io.write_line.call_args_list]
    assert any("Projects:" in line for line in lines)
    assert any("Dependency tree:" in line for line in lines)
    assert any("Publish order:" in line for line in lines)


# ---------------------------------------------------------------------------
# handle — filter flags
# ---------------------------------------------------------------------------

def test_handle_projects_flag_only_renders_projects(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    cmd, io = _make_command(di, metadata, options={"projects": True})
    cmd.handle()
    lines = [c.args[0] for c in io.write_line.call_args_list]
    assert any("Projects:" in line for line in lines)
    assert not any("Dependency tree:" in line for line in lines)
    assert not any("Publish order:" in line for line in lines)


def test_handle_dependency_tree_flag(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    cmd, io = _make_command(di, metadata, options={"dependency-tree": True})
    cmd.handle()
    lines = [c.args[0] for c in io.write_line.call_args_list]
    assert not any("Projects:" in line for line in lines)
    assert any("Dependency tree:" in line for line in lines)
    assert not any("Publish order:" in line for line in lines)


def test_handle_publish_order_flag(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    cmd, io = _make_command(di, metadata, options={"publish-order": True})
    cmd.handle()
    lines = [c.args[0] for c in io.write_line.call_args_list]
    assert not any("Projects:" in line for line in lines)
    assert not any("Dependency tree:" in line for line in lines)
    assert any("Publish order:" in line or "Wave" in line for line in lines)


def test_handle_no_deliverable_projects_shows_message(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    for meta in metadata.projects.values():
        meta.deliver = DeliverableType.DISABLED_BY_PACKAGE_MODE
    cmd, io = _make_command(di, metadata, options={"publish-order": True})
    cmd.handle()
    lines = [c.args[0] for c in io.write_line.call_args_list]
    assert any("No deliverable projects" in line for line in lines)


def test_handle_returns_zero(tmp_path):
    di, _, metadata = _setup(tmp_path, [])
    cmd, _io = _make_command(di, metadata)
    assert cmd.handle() == 0


# ---------------------------------------------------------------------------
# handle — JSON renderer
# ---------------------------------------------------------------------------

def test_handle_json_flag_outputs_json(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    cmd, io = _make_command(di, metadata, options={"json": True})
    cmd.handle()
    lines = [c.args[0] for c in io.write_line.call_args_list]
    json_line = lines[-1]
    data = json.loads(json_line)
    assert isinstance(data, dict)


def test_handle_json_with_projects_flag(tmp_path):
    di, _, metadata = _setup(tmp_path, ["lib-a"])
    cmd, io = _make_command(di, metadata, options={"json": True, "projects": True})
    cmd.handle()
    lines = [c.args[0] for c in io.write_line.call_args_list]
    data = json.loads(lines[-1])
    assert "projects" in data
    assert "dependency_tree" not in data
    assert "publish_order" not in data

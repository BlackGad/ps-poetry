import json
from unittest.mock import MagicMock

from cleo.io.io import IO

from ps.plugin.module.delivery.output import JsonDeliveryRenderer
from ps.plugin.module.delivery.output._models import (
    DependencyNode,
    DependencyResolution,
    ProjectResolution,
    ProjectSummary,
    PublishWave,
    VersionPatternResult,
)


def _make_io() -> MagicMock:
    io = MagicMock(spec=IO)
    return io


def _flush_and_parse(renderer: JsonDeliveryRenderer, io: MagicMock) -> dict:
    renderer.flush()
    raw = io.write_line.call_args.args[0]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# render_resolution
# ---------------------------------------------------------------------------

def test_render_resolution_key():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("Projects", [])
    data = _flush_and_parse(renderer, io)
    assert "projects" in data


def test_render_resolution_project_fields():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("Projects", [
        ProjectResolution(
            name="my-lib", path="/some/path", version="1.2.3",
            deliver="Enabled", pinning="compatible", matched_pattern="{spec}",
        ),
    ])
    data = _flush_and_parse(renderer, io)
    proj = data["projects"][0]
    assert proj["name"] == "my-lib"
    assert proj["path"] == "/some/path"
    assert proj["version"] == "1.2.3"
    assert proj["deliver"] == "Enabled"
    assert proj["pinning"] == "compatible"
    assert proj["matched_pattern"] == "{spec}"


def test_render_resolution_pattern_results():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(pattern="{in}", condition="{in}", condition_matched=False),
                VersionPatternResult(pattern="{spec}", matched=True, resolved_raw="1.0.0"),
            ],
        ),
    ])
    data = _flush_and_parse(renderer, io)
    patterns = data["p"][0]["pattern_results"]
    assert len(patterns) == 2
    assert patterns[0]["pattern"] == "{in}"
    assert patterns[0]["condition"] == "{in}"
    assert patterns[0]["condition_matched"] is False
    assert patterns[1]["matched"] is True
    assert patterns[1]["resolved_raw"] == "1.0.0"


def test_render_resolution_dependencies():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[
                DependencyResolution(name="lib-b", constraint=">=1.0", is_project=True, path="../lib-b", source=""),
                DependencyResolution(name="requests", constraint=">=2.0", source="direct"),
            ],
        ),
    ])
    data = _flush_and_parse(renderer, io)
    deps = data["p"][0]["dependencies"]
    assert len(deps) == 2
    assert deps[0]["name"] == "lib-b"
    assert deps[0]["is_project"] is True
    assert deps[0]["path"] == "../lib-b"
    assert deps[1]["name"] == "requests"
    assert deps[1]["source"] == "direct"


def test_render_resolution_pattern_errors():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(pattern="{bad}", errors=["error1", "error2"]),
            ],
        ),
    ])
    data = _flush_and_parse(renderer, io)
    errors = data["p"][0]["pattern_results"][0]["errors"]
    assert errors == ["error1", "error2"]


# ---------------------------------------------------------------------------
# render_dependency_tree
# ---------------------------------------------------------------------------

def test_render_dependency_tree_key():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_dependency_tree("Dependency tree", [])
    data = _flush_and_parse(renderer, io)
    assert "dependency_tree" in data


def test_render_dependency_tree_structure():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    child = DependencyNode(name="child", version="0.1.0")
    root = DependencyNode(name="parent", version="2.0.0", children=[child])
    renderer.render_dependency_tree("Tree", [root])
    data = _flush_and_parse(renderer, io)
    tree = data["tree"]
    assert len(tree) == 1
    assert tree[0]["name"] == "parent"
    assert tree[0]["version"] == "2.0.0"
    assert tree[0]["children"][0]["name"] == "child"


def test_render_dependency_tree_no_children_key_when_empty():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_dependency_tree("Tree", [DependencyNode(name="leaf", version="1.0")])
    data = _flush_and_parse(renderer, io)
    assert "children" not in data["tree"][0]


# ---------------------------------------------------------------------------
# render_publish_waves
# ---------------------------------------------------------------------------

def test_render_publish_waves_key():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_publish_waves("Publish order", [])
    data = _flush_and_parse(renderer, io)
    assert "publish_order" in data


def test_render_publish_waves_structure():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    waves = [
        PublishWave(index=1, projects=[ProjectSummary(name="a", version="1.0", deliver="")]),
        PublishWave(index=2, projects=[ProjectSummary(name="b", version="2.0", deliver="")]),
    ]
    renderer.render_publish_waves("Waves", waves)
    data = _flush_and_parse(renderer, io)
    assert len(data["waves"]) == 2
    assert data["waves"][0]["wave"] == 1
    assert data["waves"][0]["projects"][0]["name"] == "a"
    assert data["waves"][1]["wave"] == 2


# ---------------------------------------------------------------------------
# render_message / flush
# ---------------------------------------------------------------------------

def test_render_message_is_noop():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_message("text")
    io.write_line.assert_not_called()


def test_flush_outputs_json():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("P", [])
    renderer.flush()
    raw = io.write_line.call_args.args[0]
    data = json.loads(raw)
    assert isinstance(data, dict)


def test_flush_resets_data():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("P", [])
    renderer.flush()
    renderer.flush()
    second_raw = io.write_line.call_args_list[-1].args[0]
    data = json.loads(second_raw)
    assert data == {}


def test_multiple_sections_combined():
    io = _make_io()
    renderer = JsonDeliveryRenderer(io)
    renderer.render_resolution("Projects", [
        ProjectResolution(name="a", path="/p", version="1.0", deliver="Enabled"),
    ])
    renderer.render_dependency_tree("Tree", [DependencyNode(name="a", version="1.0")])
    renderer.render_publish_waves("Waves", [
        PublishWave(index=1, projects=[ProjectSummary(name="a", version="1.0", deliver="")]),
    ])
    data = _flush_and_parse(renderer, io)
    assert "projects" in data
    assert "tree" in data
    assert "waves" in data

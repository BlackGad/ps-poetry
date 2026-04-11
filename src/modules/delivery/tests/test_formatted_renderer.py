from unittest.mock import MagicMock

from cleo.io.io import IO

from ps.plugin.module.delivery.output import FormattedDeliveryRenderer
from ps.plugin.module.delivery.output._models import (
    DependencyNode,
    DependencyResolution,
    ProjectResolution,
    ProjectSummary,
    PublishWave,
    VersionPatternResult,
)


def _make_io(*, verbose: bool = False, debug: bool = False) -> MagicMock:
    io = MagicMock(spec=IO)
    io.is_verbose.return_value = verbose
    io.is_debug.return_value = debug
    return io


def _collect_lines(io: MagicMock) -> list[str]:
    return [call.args[0] for call in io.write_line.call_args_list]


def _any_line(lines: list[str], *substrings: str) -> bool:
    return any(all(s in line for s in substrings) for line in lines)


def _no_line(lines: list[str], *substrings: str) -> bool:
    return not any(all(s in line for s in substrings) for line in lines)


# ---------------------------------------------------------------------------
# render_resolution — basic
# ---------------------------------------------------------------------------

def test_render_resolution_title():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("Projects", [])
    lines = _collect_lines(io)
    assert _any_line(lines, "Projects:")


def test_render_resolution_project_name_and_path():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("Projects", [
        ProjectResolution(name="my-lib", path="/some/path", version="1.0.0", deliver="Enabled"),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "my-lib")
    assert _any_line(lines, "/some/path")


def test_render_resolution_deliver_enabled():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(name="a", path="/p", version="1.0.0", deliver="Enabled"),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "Enabled")


def test_render_resolution_deliver_disabled_by_package_mode():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(name="a", path="/p", version="1.0.0", deliver="DisabledByPackageMode"),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "Disabled (package-mode)")


def test_render_resolution_deliver_disabled_by_option():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(name="a", path="/p", version="1.0.0", deliver="DisabledByDeliverableOption"),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "Disabled (deliver option)")


def test_render_resolution_version_normal():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(name="a", path="/p", version="2.3.4", deliver="Enabled"),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "2.3.4")
    assert _no_line(lines, "Pattern:")


def test_render_resolution_version_verbose_shows_pattern_and_pinning():
    io = _make_io(verbose=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="2.3.4", deliver="Enabled",
            pinning="compatible", matched_pattern="{spec}",
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "Pattern:", "{spec}", "compatible")


# ---------------------------------------------------------------------------
# render_resolution — debug pattern details
# ---------------------------------------------------------------------------

def test_render_resolution_debug_shows_pattern_list():
    io = _make_io(debug=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(pattern="{in}", matched=False),
                VersionPatternResult(pattern="{spec}", matched=True),
            ],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "Version pattern [1]", "{in}")
    assert _any_line(lines, "Version pattern [2]", "{spec}")


def test_render_resolution_debug_condition_true():
    io = _make_io(debug=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(pattern="[{in}] {in}", condition="{in}", condition_matched=True, matched=True),
            ],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "evaluated to true")


def test_render_resolution_debug_condition_false():
    io = _make_io(debug=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(pattern="[{in}] {in}", condition="{in}", condition_matched=False, matched=False),
            ],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "evaluated to false")


def test_render_resolution_debug_condition_validation_failed():
    io = _make_io(debug=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(
                    pattern="[{bad}] {bad}", condition="{bad}",
                    condition_matched=False, matched=False,
                    errors=["some error"],
                ),
            ],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "validation failed")
    assert _any_line(lines, "some error")


def test_render_resolution_debug_patterns_not_shown_in_normal_mode():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            pattern_results=[
                VersionPatternResult(pattern="{spec}", matched=True),
            ],
        ),
    ])
    lines = _collect_lines(io)
    assert _no_line(lines, "Version pattern [")


# ---------------------------------------------------------------------------
# render_resolution — dependencies
# ---------------------------------------------------------------------------

def test_render_resolution_project_dependency():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[DependencyResolution(name="lib-b", constraint="", is_project=True, path="../lib-b")],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "Project dependency", "lib-b")


def test_render_resolution_project_dependency_verbose_shows_path():
    io = _make_io(verbose=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[DependencyResolution(name="lib-b", constraint="", is_project=True, path="../lib-b")],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "../lib-b")


def test_render_resolution_third_party_dependency():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[DependencyResolution(name="requests", constraint=">=2.0", source="direct")],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "requests", ">=2.0")


def test_render_resolution_skipped_dependency_not_shown_in_normal():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[DependencyResolution(name="dev-tool", constraint="", source="skipped")],
        ),
    ])
    lines = _collect_lines(io)
    assert _no_line(lines, "dev-tool")


def test_render_resolution_skipped_dependency_shown_in_debug():
    io = _make_io(debug=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[DependencyResolution(name="dev-tool", constraint="", source="skipped")],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "dev-tool", "skipped")


def test_render_resolution_host_dependency_verbose_shows_source():
    io = _make_io(verbose=True)
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_resolution("P", [
        ProjectResolution(
            name="a", path="/p", version="1.0.0", deliver="Enabled",
            dependencies=[DependencyResolution(name="click", constraint=">=8.0", source="host")],
        ),
    ])
    lines = _collect_lines(io)
    assert _any_line(lines, "host", "click")


# ---------------------------------------------------------------------------
# render_dependency_tree
# ---------------------------------------------------------------------------

def test_render_dependency_tree_title():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_dependency_tree("Dependency tree", [])
    lines = _collect_lines(io)
    assert _any_line(lines, "Dependency tree:")


def test_render_dependency_tree_single_root():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_dependency_tree("Tree", [DependencyNode(name="root", version="1.0.0")])
    lines = _collect_lines(io)
    assert _any_line(lines, "root", "1.0.0")


def test_render_dependency_tree_nested():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    child = DependencyNode(name="child", version="0.1.0")
    root = DependencyNode(name="parent", version="2.0.0", children=[child])
    renderer.render_dependency_tree("Tree", [root])
    lines = _collect_lines(io)
    assert _any_line(lines, "parent")
    assert _any_line(lines, "child")


def test_render_dependency_tree_uses_tree_chars():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    child = DependencyNode(name="child", version="0.1.0")
    root = DependencyNode(name="parent", version="2.0.0", children=[child])
    renderer.render_dependency_tree("Tree", [root])
    lines = _collect_lines(io)
    combined = "\n".join(lines)
    assert "└── " in combined or "├── " in combined


# ---------------------------------------------------------------------------
# render_publish_waves
# ---------------------------------------------------------------------------

def test_render_publish_waves_title():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_publish_waves("Publish order", [])
    lines = _collect_lines(io)
    assert _any_line(lines, "Publish order:")


def test_render_publish_waves_single_wave():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    wave = PublishWave(index=1, projects=[
        ProjectSummary(name="lib-a", version="1.0.0", deliver="Enabled"),
    ])
    renderer.render_publish_waves("Publish order", [wave])
    lines = _collect_lines(io)
    assert _any_line(lines, "Wave 1")
    assert _any_line(lines, "lib-a", "1.0.0")


def test_render_publish_waves_multiple_waves():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    waves = [
        PublishWave(index=1, projects=[ProjectSummary(name="a", version="1.0", deliver="")]),
        PublishWave(index=2, projects=[ProjectSummary(name="b", version="2.0", deliver="")]),
    ]
    renderer.render_publish_waves("Publish order", waves)
    lines = _collect_lines(io)
    assert _any_line(lines, "Wave 1")
    assert _any_line(lines, "Wave 2")


# ---------------------------------------------------------------------------
# render_message / flush
# ---------------------------------------------------------------------------

def test_render_message():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.render_message("hello world")
    io.write_line.assert_called_with("hello world")


def test_flush_is_noop():
    io = _make_io()
    renderer = FormattedDeliveryRenderer(io)
    renderer.flush()
    io.write_line.assert_not_called()

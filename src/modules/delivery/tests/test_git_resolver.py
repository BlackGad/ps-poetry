from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

from ps.version import Version
from ps.token_expressions.token_resolvers._instance_resolver import InstanceResolver

from ps.plugin.module.delivery.token_resolvers._git_resolver import (
    GitInfo,
    collect_git_info,
)


# ---------------------------------------------------------------------------
# GitInfo — __str__ (no args via InstanceResolver)
# ---------------------------------------------------------------------------

def test_git_info_str_returns_version_string():
    info = GitInfo(version=Version.parse("1.2.3") or Version(), sha="abc1234", distance=0, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)([]) == "1.2.3"


def test_git_info_str_fallback_version_returns_zero():
    info = GitInfo(version=Version(), sha="abc1234", distance=5, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)([]) == "0"


# ---------------------------------------------------------------------------
# GitInfo — sha accessor
# ---------------------------------------------------------------------------

def test_git_info_sha_returns_sha():
    info = GitInfo(version=Version.parse("1.0.0") or Version(), sha="deadbeef", distance=0, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)(["sha"]) == "deadbeef"


# ---------------------------------------------------------------------------
# GitInfo — distance accessor
# ---------------------------------------------------------------------------

def test_git_info_distance_returns_int():
    info = GitInfo(version=Version.parse("1.0.0") or Version(), sha="abc", distance=7, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)(["distance"]) == 7


def test_git_info_distance_zero():
    info = GitInfo(version=Version.parse("1.0.0") or Version(), sha="abc", distance=0, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)(["distance"]) == 0


# ---------------------------------------------------------------------------
# GitInfo — dirty accessor
# ---------------------------------------------------------------------------

def test_git_info_dirty_true():
    info = GitInfo(version=Version.parse("1.0.0") or Version(), sha="abc", distance=0, dirty=True, branch="main", main="main")
    assert InstanceResolver(info)(["dirty"]) is True


def test_git_info_dirty_false():
    info = GitInfo(version=Version.parse("1.0.0") or Version(), sha="abc", distance=0, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)(["dirty"]) is False


# ---------------------------------------------------------------------------
# GitInfo — version sub-accessors
# ---------------------------------------------------------------------------

def test_git_info_version_major_accessor():
    info = GitInfo(version=Version.parse("3.5.2") or Version(), sha="abc", distance=0, dirty=False, branch="feature", main="main")
    assert InstanceResolver(info)(["version", "major"]) == 3


def test_git_info_version_minor_accessor():
    info = GitInfo(version=Version.parse("3.5.2") or Version(), sha="abc", distance=0, dirty=False, branch="feature", main="main")
    assert InstanceResolver(info)(["version", "minor"]) == 5


def test_git_info_version_patch_accessor():
    info = GitInfo(version=Version.parse("3.5.2") or Version(), sha="abc", distance=0, dirty=False, branch="feature", main="main")
    assert InstanceResolver(info)(["version", "patch"]) == 2


def test_git_info_version_fallback_major_is_zero():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)(["version", "major"]) == 0


# ---------------------------------------------------------------------------
# GitInfo — branch and main accessors
# ---------------------------------------------------------------------------

def test_git_info_branch_returns_branch():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="feature/my-feature", main="main")
    assert InstanceResolver(info)(["branch"]) == "feature/my-feature"


def test_git_info_branch_none_returns_none():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch=None, main="main")
    assert InstanceResolver(info)(["branch"]) is None


def test_git_info_main_returns_main():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="feature", main="develop")
    assert InstanceResolver(info)(["main"]) == "develop"


def test_git_info_main_none_returns_none():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="feature", main=None)
    assert InstanceResolver(info)(["main"]) is None


# ---------------------------------------------------------------------------
# collect_git_info — helpers
# ---------------------------------------------------------------------------

def _make_run_result(stdout: str, returncode: int = 0) -> CompletedProcess[str]:
    result: CompletedProcess[str] = MagicMock(spec=CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    return result


def _side_effects(*responses: tuple[str, int]) -> list[CompletedProcess[str]]:
    return [_make_run_result(stdout, rc) for stdout, rc in responses]


# ---------------------------------------------------------------------------
# collect_git_info — not a git repo
# ---------------------------------------------------------------------------

def test_collect_git_info_returns_none_when_not_a_git_repo(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(("", 128))
        info = collect_git_info(tmp_path)

    assert info is None


def test_collect_git_info_returns_none_on_os_error(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run", side_effect=OSError):
        info = collect_git_info(tmp_path)

    assert info is None


# ---------------------------------------------------------------------------
# collect_git_info — happy path (with tags)
# ---------------------------------------------------------------------------

def test_collect_git_info_parses_clean_tag(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),            # rev-parse --short HEAD
            ("", 0),                   # status --porcelain (clean)
            ("v1.2.3-5-gabc1234", 0),  # describe --tags --long
            ("feature", 0),            # rev-parse --abbrev-ref HEAD
            ("origin/main", 0),        # rev-parse --abbrev-ref origin/HEAD
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.version == Version.parse("1.2.3")
    assert info.sha == "abc1234"
    assert info.distance == 5
    assert info.dirty is False
    assert info.branch == "feature"
    assert info.main == "main"


def test_collect_git_info_parses_dirty_repo(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("deadbeef", 0),            # rev-parse --short HEAD
            ("M src/file.py\n", 0),     # status --porcelain (dirty)
            ("v2.0.0-0-gdeadbeef", 0),  # describe --tags --long
            ("main", 0),                # rev-parse --abbrev-ref HEAD
            ("origin/main", 0),         # rev-parse --abbrev-ref origin/HEAD
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.version == Version.parse("2.0.0")
    assert info.sha == "deadbeef"
    assert info.distance == 0
    assert info.dirty is True
    assert info.branch == "main"
    assert info.main == "main"


def test_collect_git_info_fallback_version_when_tag_not_a_version(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),
            ("", 0),
            ("release-tag-0-gabc1234", 0),
            ("main", 0),
            ("origin/main", 0),
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.version == Version()
    assert info.sha == "abc1234"


# ---------------------------------------------------------------------------
# collect_git_info — no tags (fallback to rev-list)
# ---------------------------------------------------------------------------

def test_collect_git_info_no_tags_uses_commit_count_as_distance(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),   # rev-parse --short HEAD
            ("", 0),          # status --porcelain (clean)
            ("", 128),        # describe --tags --long (no tags)
            ("42", 0),        # rev-list --count HEAD
            ("main", 0),      # rev-parse --abbrev-ref HEAD
            ("origin/main", 0),  # rev-parse --abbrev-ref origin/HEAD
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.version == Version()
    assert info.sha == "abc1234"
    assert info.distance == 42
    assert info.dirty is False
    assert info.branch == "main"
    assert info.main == "main"


def test_collect_git_info_no_tags_distance_zero_when_rev_list_fails(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),
            ("", 0),
            ("", 128),
            ("", 128),
            ("main", 0),
            ("origin/main", 0),
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.distance == 0


# ---------------------------------------------------------------------------
# collect_git_info — describe output with unrecognized format
# ---------------------------------------------------------------------------

def test_collect_git_info_fallback_version_when_describe_unrecognized(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),
            ("", 0),
            ("not-valid-describe-output", 0),
            ("main", 0),
            ("origin/main", 0),
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.version == Version()
    assert info.sha == "abc1234"


# ---------------------------------------------------------------------------
# collect_git_info — path handling
# ---------------------------------------------------------------------------

def test_collect_git_info_uses_parent_when_path_is_file(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")

    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("aaaa0000", 0),
            ("", 0),
            ("v1.0.0-0-gaaaa0000", 0),
            ("main", 0),
            ("origin/main", 0),
        )
        collect_git_info(pyproject)

    first_call = mock_run.call_args_list[0]
    assert first_call.kwargs["cwd"] == tmp_path


# ---------------------------------------------------------------------------
# collect_git_info — branch and main
# ---------------------------------------------------------------------------

def test_collect_git_info_branch_without_origin_head(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),
            ("", 0),
            ("v1.0.0-0-gabc1234", 0),
            ("feature/my-branch", 0),  # rev-parse --abbrev-ref HEAD
            ("", 128),                 # rev-parse --abbrev-ref origin/HEAD fails
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.branch == "feature/my-branch"
    assert info.main is None


def test_collect_git_info_main_strips_origin_prefix(tmp_path: Path):
    with patch("ps.plugin.module.delivery.token_resolvers._git_resolver.subprocess.run") as mock_run:
        mock_run.side_effect = _side_effects(
            ("abc1234", 0),
            ("", 0),
            ("v1.0.0-0-gabc1234", 0),
            ("main", 0),
            ("origin/develop", 0),
        )
        info = collect_git_info(tmp_path)

    assert info is not None
    assert info.main == "develop"


# ---------------------------------------------------------------------------
# GitInfo — mainline property
# ---------------------------------------------------------------------------

def test_git_info_mainline_true_when_branch_equals_main():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="main", main="main")
    assert info.mainline is True


def test_git_info_mainline_true_when_branch_equals_non_main_default():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="develop", main="develop")
    assert info.mainline is True


def test_git_info_mainline_false_when_branch_differs_from_main():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="feature/x", main="main")
    assert info.mainline is False


def test_git_info_mainline_false_when_branch_is_none():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch=None, main="main")
    assert info.mainline is False


def test_git_info_mainline_false_when_main_is_none():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="main", main=None)
    assert info.mainline is False


def test_git_info_mainline_false_when_both_none():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch=None, main=None)
    assert info.mainline is False


def test_git_info_mainline_via_instance_resolver():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="main", main="main")
    assert InstanceResolver(info)(["mainline"]) is True


def test_git_info_mainline_via_instance_resolver_false():
    info = GitInfo(version=Version(), sha="abc", distance=0, dirty=False, branch="feature", main="main")
    assert InstanceResolver(info)(["mainline"]) is False

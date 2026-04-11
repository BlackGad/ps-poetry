import contextlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ps.version import Version

_DESCRIBE_PATTERN: re.Pattern[str] = re.compile(r"^(.+)-(\d+)-g([0-9a-f]+)$")


@dataclass
class GitInfo:
    version: Version
    sha: str
    distance: int
    dirty: bool
    branch: Optional[str]
    main: Optional[str]

    def __str__(self) -> str:
        return str(self.version)

    @property
    def mainline(self) -> bool:
        return self.branch is not None and self.main is not None and self.branch == self.main


def _run_git(args: list[str], cwd: Path) -> Optional[str]:
    cmd = ["git", *args]
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)  # noqa: S603
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return None


def _resolve_branch(cwd: Path) -> Optional[str]:
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if branch != "HEAD":
        return branch

    # Detached HEAD (e.g. CI checkout) — find a remote branch pointing at HEAD
    refs = _run_git(["branch", "-r", "--points-at", "HEAD", "--format", "%(refname:short)"], cwd)
    if refs:
        for ref in refs.splitlines():
            if ref.startswith("origin/") and ref != "origin/HEAD":
                return ref.removeprefix("origin/")
    return None


def _resolve_default_branch(cwd: Path) -> Optional[str]:
    raw = _run_git(["rev-parse", "--abbrev-ref", "origin/HEAD"], cwd)
    if raw is not None:
        return raw.removeprefix("origin/")

    # origin/HEAD not set (e.g. CI checkout) — probe common defaults
    for candidate in ("main", "master"):
        if _run_git(["rev-parse", "--verify", f"origin/{candidate}"], cwd) is not None:
            return candidate
    return None


def collect_git_info(path: Path) -> Optional[GitInfo]:
    cwd = path if path.is_dir() else path.parent

    commit_hash = _run_git(["rev-parse", "--short", "HEAD"], cwd)
    if not commit_hash:
        return None

    dirty_output = _run_git(["status", "--porcelain", "--untracked-files=no"], cwd)
    dirty = bool(dirty_output)

    version = Version()
    distance = 0

    describe = _run_git(["describe", "--tags", "--long"], cwd)
    if describe:
        m = _DESCRIBE_PATTERN.match(describe)
        if m:
            tag = m.group(1)
            distance = int(m.group(2))
            tag_version = tag[1:] if tag and tag[0] in ("v", "V") else tag
            parsed = Version.parse(tag_version)
            if parsed is not None:
                version = parsed
    else:
        count = _run_git(["rev-list", "--count", "HEAD"], cwd)
        if count:
            with contextlib.suppress(ValueError):
                distance = int(count)

    branch = _resolve_branch(cwd)
    main = _resolve_default_branch(cwd)

    return GitInfo(version=version, sha=commit_hash, distance=distance, dirty=dirty, branch=branch, main=main)

from pathlib import Path
from unittest.mock import MagicMock, patch

from cleo.io.io import IO

from ps.plugin.sdk.project import Environment, parse_project, Project
from ps.plugin.module.check.checks._imports_check import (
    ImportsCheck,
    _build_local_module_map,
    _collect_all_dep_names,
    _collect_imports,
    _collect_pypi_transitive_deps,
    _find_providers,
    _get_package_source_dirs,
)


def make_io() -> MagicMock:
    return MagicMock(spec=IO)


def make_environment(projects: list[Project]) -> Environment:
    env = MagicMock(spec=Environment)
    env.projects = projects
    return env


def make_project(tmp_path: Path, name: str, extra_toml: str = "") -> Project:
    pyproject = tmp_path / name / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        f'[project]\nname = "{name}"\nversion = "1.0.0"\n{extra_toml}\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    return project


def write_py(directory: Path, filename: str, content: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# _get_package_source_dirs
# ---------------------------------------------------------------------------

def test_get_package_source_dirs_no_packages_returns_project_dir(tmp_path):
    project = make_project(tmp_path, "my-pkg")
    result = _get_package_source_dirs(project)
    assert result == [project.path.parent]


def test_get_package_source_dirs_with_packages_from_src(tmp_path):
    project_dir = tmp_path / "my-pkg"
    project_dir.mkdir(parents=True, exist_ok=True)
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "my-pkg"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "my/module", from = "src"}]\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    result = _get_package_source_dirs(project)
    assert result == [(project_dir / "src" / "my" / "module").resolve()]


def test_get_package_source_dirs_include_without_from(tmp_path):
    project_dir = tmp_path / "my-pkg"
    project_dir.mkdir(parents=True, exist_ok=True)
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "my-pkg"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "my_module"}]\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    result = _get_package_source_dirs(project)
    assert result == [(project_dir / "my_module").resolve()]


# ---------------------------------------------------------------------------
# _collect_imports
# ---------------------------------------------------------------------------

def test_collect_imports_empty_dir_returns_empty_set(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    result = _collect_imports([src])
    assert result == {}


def test_collect_imports_import_statement(tmp_path):
    src = tmp_path / "src"
    write_py(src, "mod.py", "import requests\n")
    result = _collect_imports([src])
    assert "requests" in result
    assert any(f == src / "mod.py" for f, _ in result["requests"])


def test_collect_imports_from_import_statement(tmp_path):
    src = tmp_path / "src"
    write_py(src, "mod.py", "from pathlib import Path\n")
    result = _collect_imports([src])
    assert "pathlib" in result
    assert any(f == src / "mod.py" for f, _ in result["pathlib"])


def test_collect_imports_relative_import_ignored(tmp_path):
    src = tmp_path / "src"
    write_py(src, "mod.py", "from . import sibling\n")
    result = _collect_imports([src])
    assert result == {}


def test_collect_imports_top_level_module_only(tmp_path):
    src = tmp_path / "src"
    write_py(src, "mod.py", "import os.path\n")
    result = _collect_imports([src])
    assert "os.path" in result
    assert "os" not in result


def test_collect_imports_syntax_error_file_skipped(tmp_path):
    src = tmp_path / "src"
    write_py(src, "bad.py", "def broken(\n")
    result = _collect_imports([src])
    assert result == {}


def test_collect_imports_deduplicates_files_per_module(tmp_path):
    src = tmp_path / "src"
    write_py(src, "a.py", "import requests\nimport requests\n")
    result = _collect_imports([src])
    assert any(f == src / "a.py" for f, _ in result["requests"])


def test_collect_imports_multiple_files(tmp_path):
    src = tmp_path / "src"
    write_py(src, "a.py", "import alpha\n")
    write_py(src, "b.py", "from beta import something\n")
    result = _collect_imports([src])
    assert "alpha" in result
    assert "beta" in result


def test_collect_imports_nested_directories(tmp_path):
    src = tmp_path / "src"
    nested = src / "sub"
    write_py(nested, "c.py", "import gamma\n")
    result = _collect_imports([src])
    assert "gamma" in result


def test_collect_imports_preserves_full_module_path(tmp_path):
    src = tmp_path / "src"
    write_py(src, "mod.py", "from ps.version import Version\n")
    result = _collect_imports([src])
    assert "ps.version" in result
    assert "ps" not in result


def test_check_namespace_import_undeclared_is_detected(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "from ps.version import Version\n")
    project = parse_project(pyproject)
    assert project is not None

    dep_dir = tmp_path / "ps-version"
    dep_dir.mkdir(parents=True, exist_ok=True)
    (dep_dir / "pyproject.toml").write_text(
        '[project]\nname = "ps-version"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "ps/version", from = "src"}]\n',
        encoding="utf-8",
    )
    ps_version_project = parse_project(dep_dir / "pyproject.toml")
    assert ps_version_project is not None

    io = make_io()
    check = ImportsCheck(make_environment([project, ps_version_project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={},
    ):
        result = check.check(io, [project], fix=False)
    assert result is not None
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "ps-version" in written


def test_check_namespace_import_declared_passes(tmp_path):
    dep_dir = tmp_path / "ps-version"
    dep_dir.mkdir(parents=True, exist_ok=True)
    dep_dir_posix = dep_dir.as_posix()
    (dep_dir / "pyproject.toml").write_text(
        '[project]\nname = "ps-version"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "ps/version", from = "src"}]\n',
        encoding="utf-8",
    )
    ps_version_project = parse_project(dep_dir / "pyproject.toml")
    assert ps_version_project is not None

    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        f'[project]\nname = "proj"\nversion = "1.0.0"\n\n'
        f'[tool.poetry.dependencies]\nps-version = {{path = "{dep_dir_posix}", develop = true}}\n',
        encoding="utf-8",
    )
    write_py(project_dir, "mod.py", "from ps.version import Version\n")
    project = parse_project(pyproject)
    assert project is not None

    check = ImportsCheck(make_environment([project, ps_version_project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


def test_check_self_import_is_not_flagged(tmp_path):
    project_dir = tmp_path / "mypkg"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "pyproject.toml").write_text(
        '[project]\nname = "my-pkg"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "my/pkg", from = "src"}]\n',
        encoding="utf-8",
    )
    write_py(project_dir, "mod.py", "from my.pkg import something\n")
    project = parse_project(project_dir / "pyproject.toml")
    assert project is not None
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"my.pkg": ["my-pkg"]},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


# ---------------------------------------------------------------------------
# _build_local_module_map / _find_providers
# ---------------------------------------------------------------------------

def test_build_local_module_map_with_packages_declaration(tmp_path):
    project_dir = tmp_path / "pkg"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "pyproject.toml").write_text(
        '[project]\nname = "ps-version"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "ps/version", from = "src"}]\n',
        encoding="utf-8",
    )
    project = parse_project(project_dir / "pyproject.toml")
    assert project is not None
    result = _build_local_module_map([project])
    assert result == {"ps.version": ["ps-version"]}


def test_build_local_module_map_no_packages_declaration(tmp_path):
    project = make_project(tmp_path, "proj")
    result = _build_local_module_map([project])
    assert result == {}


def test_find_providers_exact_local_match():
    local_map = {"ps.version": ["ps-version"]}
    result = _find_providers("ps.version", local_map, {})
    assert result == ["ps-version"]


def test_find_providers_prefix_local_match():
    local_map = {"ps.version": ["ps-version"]}
    result = _find_providers("ps.version.constraint", local_map, {})
    assert result == ["ps-version"]


def test_find_providers_falls_back_to_dist_map():
    result = _find_providers("requests", {}, {"requests": ["requests"]})
    assert result == ["requests"]


def test_find_providers_local_takes_priority_over_dist_map():
    local_map = {"ps.version": ["ps-version"]}
    dist_map = {"ps": ["other-pkg"]}
    result = _find_providers("ps.version", local_map, dist_map)
    assert result == ["ps-version"]


def test_find_providers_not_found_returns_none():
    result = _find_providers("unknown.module", {}, {})
    assert result is None


def test_collect_all_dep_names_no_deps(tmp_path):
    project = make_project(tmp_path, "proj")
    result = _collect_all_dep_names([], project)
    assert result == set()


def test_collect_all_dep_names_simple_dep(tmp_path):
    project = make_project(
        tmp_path,
        "proj",
        '[tool.poetry.dependencies]\nrequests = "^2.0"',
    )
    result = _collect_all_dep_names([], project)
    assert "requests" in result


def test_collect_all_dep_names_normalizes_hyphens(tmp_path):
    project = make_project(
        tmp_path,
        "proj",
        '[tool.poetry.dependencies]\nmy-lib = "^1.0"',
    )
    result = _collect_all_dep_names([], project)
    assert "my_lib" in result


def test_collect_all_dep_names_transient_path_dep(tmp_path):
    dep_dir = tmp_path / "dep-pkg"
    dep_dir.mkdir(parents=True, exist_ok=True)
    (dep_dir / "pyproject.toml").write_text(
        '[project]\nname = "dep-pkg"\nversion = "1.0.0"\n\n'
        '[tool.poetry.dependencies]\ntransit-lib = "^1.0"\n',
        encoding="utf-8",
    )
    dep_project = parse_project(dep_dir / "pyproject.toml")
    assert dep_project is not None

    project_dir = tmp_path / "main-pkg"
    project_dir.mkdir(parents=True, exist_ok=True)
    dep_dir_posix = dep_dir.as_posix()
    (project_dir / "pyproject.toml").write_text(
        f'[project]\nname = "main-pkg"\nversion = "1.0.0"\n\n'
        f'[tool.poetry.dependencies]\ndep-pkg = {{path = "{dep_dir_posix}", develop = true}}\n',
        encoding="utf-8",
    )
    project = parse_project(project_dir / "pyproject.toml")
    assert project is not None
    result = _collect_all_dep_names([dep_project], project)
    assert "transit_lib" in result


# ---------------------------------------------------------------------------
# _collect_pypi_transitive_deps
# ---------------------------------------------------------------------------

def test_collect_pypi_transitive_deps_unknown_package_returns_empty():
    with patch(
        "ps.plugin.module.check.checks._imports_check.metadata_requires",
        side_effect=__import__("importlib.metadata", fromlist=["PackageNotFoundError"]).PackageNotFoundError,
    ):
        result = _collect_pypi_transitive_deps("nonexistent", {}, set())
    assert result == set()


def test_collect_pypi_transitive_deps_direct_dep():
    with patch(
        "ps.plugin.module.check.checks._imports_check.metadata_requires",
        return_value=["cleo (>=2.1.0,<3.0.0)"],
    ):
        result = _collect_pypi_transitive_deps("poetry", {}, set())
    assert "cleo" in result


def test_collect_pypi_transitive_deps_uses_cache():
    cache: dict = {"poetry": {"cached_dep"}}
    result = _collect_pypi_transitive_deps("poetry", cache, set())
    assert result == {"cached_dep"}


def test_collect_pypi_transitive_deps_handles_cycle():
    call_count = 0

    def fake_requires(name: str) -> list[str]:
        nonlocal call_count
        call_count += 1
        if name.lower() == "a":
            return ["B"]
        return ["A"]

    with patch(
        "ps.plugin.module.check.checks._imports_check.metadata_requires",
        side_effect=fake_requires,
    ):
        result = _collect_pypi_transitive_deps("A", {}, set())
    assert "b" in result
    assert call_count == 2


def test_collect_all_dep_names_includes_pypi_transitive(tmp_path):
    project = make_project(
        tmp_path,
        "proj",
        '[tool.poetry.dependencies]\npoetry = "^2.0"',
    )
    with patch(
        "ps.plugin.module.check.checks._imports_check.metadata_requires",
        return_value=["cleo (>=2.1.0)"],
    ):
        result = _collect_all_dep_names([], project)
    assert "cleo" in result


def test_collect_all_dep_names_pypi_cache_shared_across_projects(tmp_path):
    proj_a = make_project(tmp_path, "proj-a", '[tool.poetry.dependencies]\npoetry = "^2.0"')
    proj_b = make_project(tmp_path, "proj-b", '[tool.poetry.dependencies]\npoetry = "^2.0"')
    pypi_cache: dict = {}
    call_count = 0

    def fake_requires(name: str) -> list[str]:
        nonlocal call_count
        call_count += 1
        return ["cleo (>=2.1.0)"] if name.lower() == "poetry" else []

    with patch(
        "ps.plugin.module.check.checks._imports_check.metadata_requires",
        side_effect=fake_requires,
    ):
        _collect_all_dep_names([], proj_a, _pypi_cache=pypi_cache)
        _collect_all_dep_names([], proj_b, _pypi_cache=pypi_cache)

    assert call_count == 2  # poetry + cleo, not repeated for second project


# ---------------------------------------------------------------------------
# ImportsCheck.check
# ---------------------------------------------------------------------------

def test_check_no_projects_returns_none():
    check = ImportsCheck(make_environment([]))
    result = check.check(make_io(), [], fix=False)
    assert result is None


def test_check_no_py_files_returns_none(tmp_path):
    project = make_project(tmp_path, "proj")
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


def test_check_stdlib_import_returns_none(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "import os\nimport sys\n")
    project = parse_project(pyproject)
    assert project is not None
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


def test_check_import_with_declared_dep_returns_none(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        '[project]\nname = "proj"\nversion = "1.0.0"\n\n'
        '[tool.poetry.dependencies]\nrequests = "^2.0"\n',
        encoding="utf-8",
    )
    write_py(project_dir, "mod.py", "import requests\n")
    project = parse_project(pyproject)
    assert project is not None
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"requests": ["requests"]},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


def test_check_import_with_no_known_distribution_returns_none(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "import unknown_local_module\n")
    project = parse_project(pyproject)
    assert project is not None
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


def test_check_undeclared_import_output_contains_pyproject_path(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "import requests\n")
    project = parse_project(pyproject)
    assert project is not None
    io = make_io()
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"requests": ["requests"]},
    ):
        check.check(io, [project], fix=False)
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert str(pyproject) in written


def test_check_undeclared_import_output_contains_py_file_path(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "import requests\n")
    project = parse_project(pyproject)
    assert project is not None
    io = make_io()
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"requests": ["requests"]},
    ):
        check.check(io, [project], fix=False)
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "mod.py" in written


def test_check_undeclared_import_returns_exception(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "import requests\n")
    project = parse_project(pyproject)
    assert project is not None
    io = make_io()
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"requests": ["requests"]},
    ):
        result = check.check(io, [project], fix=False)
    assert result is not None
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "requests" in written


def test_check_undeclared_import_writes_error_line(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text('[project]\nname = "proj"\nversion = "1.0.0"\n', encoding="utf-8")
    write_py(project_dir, "mod.py", "import requests\n")
    project = parse_project(pyproject)
    assert project is not None
    io = make_io()
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"requests": ["requests"]},
    ):
        check.check(io, [project], fix=False)
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "requests" in written


def test_check_import_with_hyphen_normalized_dep_returns_none(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        '[project]\nname = "proj"\nversion = "1.0.0"\n\n'
        '[tool.poetry.dependencies]\nmy-lib = "^1.0"\n',
        encoding="utf-8",
    )
    write_py(project_dir, "mod.py", "import my_lib\n")
    project = parse_project(pyproject)
    assert project is not None
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"my_lib": ["my-lib"]},
    ):
        result = check.check(make_io(), [project], fix=False)
    assert result is None


def test_check_passes_success_message_when_no_errors(tmp_path):
    project = make_project(tmp_path, "proj")
    io = make_io()
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={},
    ):
        check.check(io, [project], fix=False)
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert "passed" in written


def test_check_uses_packages_source_dirs(tmp_path):
    project_dir = tmp_path / "proj"
    pyproject = project_dir / "pyproject.toml"
    pyproject.parent.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(
        '[project]\nname = "proj"\nversion = "1.0.0"\n\n'
        '[tool.poetry]\npackages = [{include = "mypkg", from = "src"}]\n',
        encoding="utf-8",
    )
    src_pkg = project_dir / "src" / "mypkg"
    write_py(src_pkg, "mod.py", "import requests\n")
    # Also put an unrelated file outside the declared package directory
    write_py(project_dir, "outside.py", "import flask\n")
    project = parse_project(pyproject)
    assert project is not None
    io = make_io()
    check = ImportsCheck(make_environment([project]))
    with patch(
        "ps.plugin.module.check.checks._imports_check.packages_distributions",
        return_value={"requests": ["requests"], "flask": ["Flask"]},
    ):
        result = check.check(io, [project], fix=False)
    # Only mypkg/mod.py should be scanned; outside.py should be ignored
    written = "\n".join(call.args[0] for call in io.write_line.call_args_list)
    assert result is not None
    assert "requests" in written
    assert "flask" not in written

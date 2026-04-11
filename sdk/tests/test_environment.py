import os
from pathlib import Path

from ps.plugin.sdk.project import Environment


def _write_pyproject(path: Path, name: str, deps: list[tuple[str, Path]] | None = None) -> Path:
    pyproject = path / "pyproject.toml"
    path.mkdir(parents=True, exist_ok=True)
    dep_lines = ""
    for dep_name, dep_path in (deps or []):
        rel = os.path.relpath(dep_path, path).replace("\\", "/")
        dep_lines += f'\n{dep_name} = {{path = "{rel}", develop = true}}'
    pyproject.write_text(
        f'[tool.poetry]\nname = "{name}"\nversion = "1.0.0"\n\n'
        f"[tool.poetry.dependencies]\npython = \"^3.10\"{dep_lines}\n",
        encoding="utf-8",
    )
    return pyproject


# ---------------------------------------------------------------------------
# Environment.project_dependencies
# ---------------------------------------------------------------------------


def test_project_dependencies_no_local_deps(tmp_path):
    pyproject = _write_pyproject(tmp_path / "a", "pkg-a")
    env = Environment(pyproject)
    project = next(p for p in env.projects if p.name.value == "pkg-a")
    assert env.project_dependencies(project) == []


def test_project_dependencies_returns_local_dep(tmp_path):
    lib_dir = tmp_path / "lib"
    _write_pyproject(lib_dir, "lib")
    app_dir = tmp_path / "app"
    _write_pyproject(app_dir, "app", deps=[("lib", lib_dir)])

    env = Environment(app_dir / "pyproject.toml")
    app = next(p for p in env.projects if p.name.value == "app")
    lib = next(p for p in env.projects if p.name.value == "lib")
    deps = env.project_dependencies(app)
    assert lib in deps
    assert len(deps) == 1


def test_project_dependencies_does_not_include_third_party(tmp_path):
    _write_pyproject(tmp_path / "a", "pkg-a")
    content = (tmp_path / "a" / "pyproject.toml").read_text(encoding="utf-8")
    content += '\nrequests = "*"\n'
    (tmp_path / "a" / "pyproject.toml").write_text(content, encoding="utf-8")
    env = Environment(tmp_path / "a" / "pyproject.toml")
    project = next(p for p in env.projects if p.name.value == "pkg-a")
    assert env.project_dependencies(project) == []


# ---------------------------------------------------------------------------
# Environment.sorted_projects
# ---------------------------------------------------------------------------


def test_sorted_projects_single_project(tmp_path):
    pyproject = _write_pyproject(tmp_path / "a", "pkg-a")
    env = Environment(pyproject)
    projects = list(env.projects)
    result = env.sorted_projects(projects)
    assert result == projects


def test_sorted_projects_dep_comes_before_dependent(tmp_path):
    lib_dir = tmp_path / "lib"
    _write_pyproject(lib_dir, "lib")
    app_dir = tmp_path / "app"
    _write_pyproject(app_dir, "app", deps=[("lib", lib_dir)])

    env = Environment(app_dir / "pyproject.toml")
    projects = list(env.projects)
    result = env.sorted_projects(projects)
    lib = next(p for p in result if p.name.value == "lib")
    app = next(p for p in result if p.name.value == "app")
    assert result.index(lib) < result.index(app)


def test_sorted_projects_chain_ordered(tmp_path):
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    c_dir = tmp_path / "c"
    _write_pyproject(a_dir, "pkg-a")
    _write_pyproject(b_dir, "pkg-b", deps=[("pkg-a", a_dir)])
    _write_pyproject(c_dir, "pkg-c", deps=[("pkg-b", b_dir)])

    env = Environment(c_dir / "pyproject.toml")
    projects = list(env.projects)
    result = env.sorted_projects(projects)
    names = [p.name.value for p in result]
    assert names.index("pkg-a") < names.index("pkg-b")
    assert names.index("pkg-b") < names.index("pkg-c")


def test_sorted_projects_subset_only_considers_given(tmp_path):
    lib_dir = tmp_path / "lib"
    _write_pyproject(lib_dir, "lib")
    app_dir = tmp_path / "app"
    _write_pyproject(app_dir, "app", deps=[("lib", lib_dir)])

    env = Environment(app_dir / "pyproject.toml")
    app = next(p for p in env.projects if p.name.value == "app")
    result = env.sorted_projects([app])
    assert result == [app]



from pathlib import Path
from typing import Any

from ps.plugin.sdk.project import Project, ProjectDependency, normalize_dist_name, dist_name_variants, parse_project


# --- normalize_dist_name ---


def test_normalize_dist_name_lowercases():
    assert normalize_dist_name("MyPackage") == "mypackage"


def test_normalize_dist_name_replaces_hyphens():
    assert normalize_dist_name("my-package") == "my_package"


def test_normalize_dist_name_replaces_dots():
    assert normalize_dist_name("my.package") == "my_package"


def test_normalize_dist_name_mixed():
    assert normalize_dist_name("My-Pkg.Name") == "my_pkg_name"


# --- dist_name_variants ---


def test_dist_name_variants_contains_original_lower():
    variants = dist_name_variants("MyPkg")
    assert "mypkg" in variants


def test_dist_name_variants_contains_underscored():
    variants = dist_name_variants("my-pkg")
    assert "my_pkg" in variants


def test_dist_name_variants_contains_hyphenated():
    variants = dist_name_variants("my_pkg")
    assert "my-pkg" in variants


def test_dist_name_variants_three_forms():
    variants = dist_name_variants("ps-version")
    assert variants == {"ps-version", "ps_version"}


# --- ProjectDependency.resolved_project_path ---


def test_resolved_project_path_none_when_no_path(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "a"\nversion = "1.0"\n\n[tool.poetry.dependencies]\nrequests = "^2.0"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    dep = project.dependencies[0]
    assert dep.path is None
    assert dep.resolved_project_path is None


def test_resolved_project_path_directory_appends_pyproject(tmp_path):
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    (lib_dir / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "lib"\nversion = "0.1"\n',
        encoding="utf-8",
    )

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "a"\nversion = "1.0"\n\n[tool.poetry.dependencies]\nlib = {path = "lib", develop = true}\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    dep = project.dependencies[0]
    assert dep.resolved_project_path == (lib_dir / "pyproject.toml").resolve()


def test_resolved_project_path_toml_file_resolves_directly(tmp_path):
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    lib_toml = lib_dir / "pyproject.toml"
    lib_toml.write_text('[tool.poetry]\nname = "lib"\nversion = "0.1"\n', encoding="utf-8")

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "a"\nversion = "1.0"\n\n[tool.poetry.dependencies]\nlib = {path = "lib/pyproject.toml", develop = true}\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    dep = project.dependencies[0]
    assert dep.resolved_project_path == lib_toml.resolve()


# --- Project.source_dirs ---


def test_source_dirs_defaults_to_project_dir(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.poetry]\nname = "a"\nversion = "1.0"\n', encoding="utf-8")
    project = parse_project(pyproject)
    assert project is not None
    assert project.source_dirs == [tmp_path]


def test_source_dirs_reads_packages_include(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "a"\nversion = "1.0"\n\n[[tool.poetry.packages]]\ninclude = "mypackage"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    assert project.source_dirs == [(tmp_path / "mypackage").resolve()]


def test_source_dirs_reads_packages_from(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "a"\nversion = "1.0"\n\n[[tool.poetry.packages]]\ninclude = "mypackage"\nfrom = "src"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    assert project.source_dirs == [(src_dir / "mypackage").resolve()]


def test_source_dirs_multiple_packages(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.poetry]\nname = "a"\nversion = "1.0"\n\n'
        '[[tool.poetry.packages]]\ninclude = "pkg_a"\n\n'
        '[[tool.poetry.packages]]\ninclude = "pkg_b"\nfrom = "src"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    assert project.source_dirs == [
        (tmp_path / "pkg_a").resolve(),
        (tmp_path / "src" / "pkg_b").resolve(),
    ]


# --- Project.add_dependency ---


def _make_poetry_project(tmp_path: Path, name: str = "my-pkg") -> Project:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        f'[tool.poetry]\nname = "{name}"\nversion = "1.0"\n\n[tool.poetry.dependencies]\npython = "^3.10"\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    return project


def test_add_dependency_pypi_adds_to_main_deps(tmp_path):
    project = _make_poetry_project(tmp_path)
    project.add_dependency("requests", constraint="^2.0")
    doc: Any = project.document
    saved = doc["tool"]["poetry"]["dependencies"]
    assert "requests" in saved
    assert saved["requests"] == "^2.0"


def test_add_dependency_pypi_default_wildcard_when_no_constraint(tmp_path):
    project = _make_poetry_project(tmp_path)
    project.add_dependency("requests")
    doc: Any = project.document
    saved = doc["tool"]["poetry"]["dependencies"]
    assert saved["requests"] == "*"


def test_add_development_dependency_local_path_uses_relative(tmp_path):
    project = _make_poetry_project(tmp_path)
    dep_dir = tmp_path / "lib"
    dep_dir.mkdir()
    project.add_development_dependency("my-lib", dep_dir)
    doc: Any = project.document
    saved = doc["tool"]["poetry"]["dependencies"]["my-lib"]
    assert saved["path"] == "lib"
    assert saved["develop"] is True


def test_add_development_dependency_sibling_uses_relative(tmp_path):
    project_dir = tmp_path / "project_a"
    project_dir.mkdir()
    project = _make_poetry_project(project_dir)
    dep_dir = tmp_path / "project_b"
    dep_dir.mkdir()
    project.add_development_dependency("my-lib", dep_dir)
    doc: Any = project.document
    saved = doc["tool"]["poetry"]["dependencies"]["my-lib"]
    assert saved["path"] == "../project_b"


def test_add_dependency_group_adds_to_group_deps(tmp_path):
    project = _make_poetry_project(tmp_path)
    project.add_dependency("pytest", constraint="^8.0", group="dev")
    doc: Any = project.document
    saved = doc["tool"]["poetry"]["group"]["dev"]["dependencies"]
    assert "pytest" in saved
    assert saved["pytest"] == "^8.0"


def test_add_dependency_returns_project_dependency(tmp_path):
    project = _make_poetry_project(tmp_path)
    dep = project.add_dependency("requests", constraint="^2.0")
    assert isinstance(dep, ProjectDependency)
    assert dep.name == "requests"


def test_add_dependency_appends_to_project_dependencies_list(tmp_path):
    project = _make_poetry_project(tmp_path)
    initial_count = len(project.dependencies)
    project.add_dependency("requests", constraint="^2.0")
    assert len(project.dependencies) == initial_count + 1
    assert any(d.name == "requests" for d in project.dependencies)


def test_add_dependency_save_persists_to_file(tmp_path):
    project = _make_poetry_project(tmp_path)
    project.add_dependency("requests", constraint="^2.0")
    project.save()
    content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert "requests" in content
    assert "^2.0" in content


def test_add_dependency_out_of_order_toml_structure(tmp_path):
    # Mirrors real-world pyproject.toml where [tool.poetry.group.*] appears
    # before [tool.poetry], causing tomlkit to return OutOfOrderTableProxy.
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "my-pkg"\n'
        'version = "1.0"\n\n'
        "[tool.poetry.group.dev.dependencies]\n"
        'pytest = "^8.0"\n\n'
        "[tool.poetry]\n"
        'packages = [{include = "my_pkg"}]\n',
        encoding="utf-8",
    )
    project = parse_project(pyproject)
    assert project is not None
    # Must not raise 'OutOfOrderTableProxy' object has no attribute 'append'
    project.add_dependency("requests", constraint="^2.0")
    doc: Any = project.document
    saved = doc["tool"]["poetry"]["dependencies"]
    assert "requests" in saved

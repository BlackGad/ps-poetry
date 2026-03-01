from pathlib import Path
from tomlkit import parse
from packaging.specifiers import SpecifierSet

from ps.plugin.sdk.helpers.toml import parse_dependencies_from_document


def test_simple_string_dependency():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.32"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "requests"
    assert deps[0].version == "^2.32"
    assert deps[0].group is None


def test_multiple_string_dependencies():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.32"
numpy = "^1.24"
pandas = "^2.0"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 3
    names = [d.name for d in deps]
    assert "requests" in names
    assert "numpy" in names
    assert "pandas" in names


def test_dict_dependency_with_version():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mypackage = { version = "^1.0", optional = true }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mypackage"
    assert deps[0].version == "^1.0"
    assert deps[0].optional is True


def test_path_dependency():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mylocal = { path = "../mylocal", develop = true }
"""
    document = parse(content)
    project_path = Path("myproject/pyproject.toml").resolve()
    deps = parse_dependencies_from_document(document, project_path)

    assert len(deps) == 1
    assert deps[0].name == "mylocal"
    assert deps[0].path == (project_path.parent / "../mylocal").resolve()
    assert deps[0].develop is True


def test_git_dependency():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mygit = { git = "https://github.com/user/repo.git", branch = "main" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mygit"
    assert deps[0].git == "https://github.com/user/repo.git"
    assert deps[0].branch == "main"


def test_git_dependency_with_tag():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mygit = { git = "https://github.com/user/repo.git", tag = "v1.0.0" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].git == "https://github.com/user/repo.git"
    assert deps[0].tag == "v1.0.0"


def test_git_dependency_with_rev():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mygit = { git = "https://github.com/user/repo.git", rev = "abc123" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].git == "https://github.com/user/repo.git"
    assert deps[0].rev == "abc123"


def test_url_dependency():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
myurl = { url = "https://example.com/package.whl" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "myurl"
    assert deps[0].url == "https://example.com/package.whl"


def test_dependency_with_extras():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = { version = "^2.32", extras = ["security", "socks"] }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "requests"
    assert deps[0].extras == ["security", "socks"]


def test_dependency_with_markers():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
pywin32 = { version = "^306", markers = "sys_platform == 'win32'" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "pywin32"
    assert deps[0].markers == "sys_platform == 'win32'"


def test_dependency_with_python_constraint():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
typing-extensions = { version = "^4.0", python = "^3.8" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "typing-extensions"
    assert deps[0].python == "^3.8"


def test_dependency_with_source():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mypkg = { version = "^1.0", source = "private-repo" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mypkg"
    assert deps[0].source == "private-repo"


def test_grouped_dependencies():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.32"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
ruff = "^0.8"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 3

    main_deps = [d for d in deps if d.group is None]
    dev_deps = [d for d in deps if d.group == "dev"]

    assert len(main_deps) == 1
    assert len(dev_deps) == 2
    assert main_deps[0].name == "requests"
    assert any(d.name == "pytest" for d in dev_deps)
    assert any(d.name == "ruff" for d in dev_deps)


def test_multiple_groups():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.32"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"

[tool.poetry.group.docs.dependencies]
sphinx = "^7.0"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 3
    groups = {d.group for d in deps}
    assert groups == {None, "dev", "docs"}


def test_empty_dependencies():
    content = """
[tool.poetry]
name = "my-package"
version = "1.0.0"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 0


def test_dict_dependency_without_version():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mypath = { path = "../mypath" }
"""
    document = parse(content)
    project_path = Path("myproject/pyproject.toml").resolve()
    deps = parse_dependencies_from_document(document, project_path)

    assert len(deps) == 1
    assert deps[0].name == "mypath"
    assert deps[0].version is None
    assert deps[0].path == (project_path.parent / "../mypath").resolve()


def test_path_dependency_absolute():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mylocal = { path = "%s" }
"""
    abs_path = Path("/absolute/path/to/package").resolve()
    content = content % str(abs_path).replace("\\", "/")
    document = parse(content)
    project_path = Path("myproject/pyproject.toml").resolve()
    deps = parse_dependencies_from_document(document, project_path)

    assert len(deps) == 1
    assert deps[0].name == "mylocal"
    assert deps[0].path == abs_path


def test_path_dependency_without_project_path():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mylocal = { path = "../mylocal" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mylocal"
    assert deps[0].path == Path("../mylocal")


def test_update_path_dependency_to_version():
    """Test updating a path dependency (no version) to a version string."""
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mylocal = { path = "../mylocal" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mylocal"
    assert deps[0].version is None
    assert deps[0].path is not None

    # Update to version string
    deps[0].update_version("^1.0.0")
    assert deps[0].version == "^1.0.0"
    assert document["tool"]["poetry"]["dependencies"]["mylocal"] == "^1.0.0"  # type: ignore[index]


def test_update_path_dependency_with_develop_to_version():
    """Test updating a path dependency with develop=true to a version string."""
    content = """
[tool.poetry.dependencies]
python = "^3.10"
ps-version = { path = "../../libraries/version", develop = true }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "ps-version"
    assert deps[0].version is None
    assert deps[0].path is not None
    assert deps[0].develop is True

    # Update to version string - source dependency is replaced with plain constraint
    deps[0].update_version("^1.0.0")
    assert deps[0].version == "^1.0.0"

    # Verify document updated correctly
    assert document["tool"]["poetry"]["dependencies"]["ps-version"] == "^1.0.0"  # type: ignore[index]


def test_update_path_dependency_to_specifier_set():
    """Test updating a path dependency using SpecifierSet."""
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mylocal = { path = "../mylocal", develop = true }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].version is None

    # Update using SpecifierSet
    deps[0].update_version(SpecifierSet(">=1.0.0,<2.0.0"))
    # SpecifierSet normalizes the order
    assert deps[0].version in (">=1.0.0,<2.0.0", "<2.0.0,>=1.0.0")
    dep_version = document["tool"]["poetry"]["dependencies"]["mylocal"]  # type: ignore[index]
    assert dep_version in (">=1.0.0,<2.0.0", "<2.0.0,>=1.0.0")


def test_update_git_dependency_to_version_replaces_with_string():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mygit = { git = "https://github.com/user/repo.git", rev = "abc123" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mygit"
    assert deps[0].version is None

    deps[0].update_version("^1.2.3")

    assert deps[0].version == "^1.2.3"
    assert document["tool"]["poetry"]["dependencies"]["mygit"] == "^1.2.3"  # type: ignore[index]


def test_update_url_dependency_to_specifier_set_replaces_with_string():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
myurl = { url = "https://example.com/package.whl" }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "myurl"
    assert deps[0].version is None

    deps[0].update_version(SpecifierSet(">=2.0.0,<3.0.0"))

    assert deps[0].version in (">=2.0.0,<3.0.0", "<3.0.0,>=2.0.0")
    dep_value = document["tool"]["poetry"]["dependencies"]["myurl"]  # type: ignore[index]
    assert dep_value in (">=2.0.0,<3.0.0", "<3.0.0,>=2.0.0")


def test_update_regular_dict_dependency_keeps_dict_and_updates_version_key():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
mypackage = { version = "^1.0", optional = true }
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].name == "mypackage"
    assert deps[0].optional is True

    deps[0].update_version("^2.0")

    dep_dict = document["tool"]["poetry"]["dependencies"]["mypackage"]  # type: ignore[index]
    assert dep_dict["version"] == "^2.0"  # type: ignore[index]
    assert dep_dict["optional"] is True  # type: ignore[index]


def test_version_constraint_converts_caret_syntax():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
package1 = "^1.2.3"
package2 = "^0.2.3"
package3 = "^0.0.3"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    # ^1.2.3 should become >=1.2.3,<2.0.0
    package1 = next(d for d in deps if d.name == "package1")
    assert package1.version == "^1.2.3"
    constraint1 = package1.version_constraint
    assert constraint1 is not None
    assert str(constraint1) in (">=1.2.3,<2.0.0", "<2.0.0,>=1.2.3")

    # ^0.2.3 should become >=0.2.3,<0.3.0
    package2 = next(d for d in deps if d.name == "package2")
    assert package2.version == "^0.2.3"
    constraint2 = package2.version_constraint
    assert constraint2 is not None
    assert str(constraint2) in (">=0.2.3,<0.3.0", "<0.3.0,>=0.2.3")

    # ^0.0.3 should become >=0.0.3,<0.0.4
    package3 = next(d for d in deps if d.name == "package3")
    assert package3.version == "^0.0.3"
    constraint3 = package3.version_constraint
    assert constraint3 is not None
    assert str(constraint3) in (">=0.0.3,<0.0.4", "<0.0.4,>=0.0.3")

from pathlib import Path
from tomlkit import parse

from ps.plugin.sdk.helpers.parse_toml import parse_dependencies_from_document


def test_simple_string_dependency():
    content = """
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.32"
"""
    document = parse(content)
    deps = parse_dependencies_from_document(document)

    assert len(deps) == 1
    assert deps[0].defined_name == "requests"
    assert deps[0].defined_version == "^2.32"
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
    names = [d.defined_name for d in deps]
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
    assert deps[0].defined_name == "mypackage"
    assert deps[0].defined_version == "^1.0"
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
    assert deps[0].defined_name == "mylocal"
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
    assert deps[0].defined_name == "mygit"
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
    assert deps[0].defined_name == "myurl"
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
    assert deps[0].defined_name == "requests"
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
    assert deps[0].defined_name == "pywin32"
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
    assert deps[0].defined_name == "typing-extensions"
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
    assert deps[0].defined_name == "mypkg"
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
    assert main_deps[0].defined_name == "requests"
    assert any(d.defined_name == "pytest" for d in dev_deps)
    assert any(d.defined_name == "ruff" for d in dev_deps)


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
    assert deps[0].defined_name == "mypath"
    assert deps[0].defined_version is None
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
    assert deps[0].defined_name == "mylocal"
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
    assert deps[0].defined_name == "mylocal"
    assert deps[0].path == Path("../mylocal")

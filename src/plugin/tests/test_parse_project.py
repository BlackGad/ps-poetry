from ps.plugin.core.parse_toml import parse_project


def test_parse_project_with_pep621_format(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    content = """
[project]
name = "test-project"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.32"
"""
    pyproject.write_text(content, encoding='utf-8')

    project = parse_project(pyproject)

    assert project.defined_name == "test-project"
    assert project.defined_version == "1.0.0"
    assert project.path == pyproject
    assert len(project.dependencies) == 1
    assert project.dependencies[0].defined_name == "requests"


def test_parse_project_with_poetry_format(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    content = """
[tool.poetry]
name = "poetry-project"
version = "2.0.0"

[tool.poetry.dependencies]
python = "^3.10"
numpy = "^1.24"
"""
    pyproject.write_text(content, encoding='utf-8')

    project = parse_project(pyproject)

    assert project.defined_name == "poetry-project"
    assert project.defined_version == "2.0.0"
    assert len(project.dependencies) == 1
    assert project.dependencies[0].defined_name == "numpy"


def test_parse_project_preserves_document(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    content = """
[project]
name = "test-project"
version = "1.0.0"

[tool.custom]
setting = "value"
"""
    pyproject.write_text(content, encoding='utf-8')

    project = parse_project(pyproject)

    assert project.document is not None
    assert "tool" in project.document
    assert "custom" in project.document["tool"]  # type: ignore[operator]

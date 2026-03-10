from tomlkit import parse

from ps.plugin.sdk import (
    parse_dependencies_from_document,
    parse_plugin_settings_from_document,
    parse_sources_from_document,
)


def main() -> None:
    content = """
[project]
name = "my-package"
version = "1.0.0"
dependencies = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
]

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"

[[tool.poetry.source]]
name = "pypi"
url = "https://pypi.org/simple/"
priority = "default"

[tool.ps-plugin]
enabled = true
"""
    document = parse(content)

    print("Dependencies:")
    for dep in parse_dependencies_from_document(document):
        version_str = dep.version or "(any)"
        print(f"  {dep.name} {version_str} group={dep.group}")

    print("\nSources:")
    for src in parse_sources_from_document(document):
        print(f"  {src.name}: {src.url} ({src.priority})")

    settings = parse_plugin_settings_from_document(document)
    print(f"\nPlugin enabled: {settings.enabled}")


if __name__ == "__main__":
    main()

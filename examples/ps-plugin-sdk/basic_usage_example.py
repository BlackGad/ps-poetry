from tomlkit import parse

from ps.plugin.sdk.project import parse_name_from_document, parse_version_from_document


def main() -> None:
    content = '[project]\nname = "my-package"\nversion = "1.2.3"\n'
    document = parse(content)

    print(parse_name_from_document(document).value)
    print(parse_version_from_document(document).value)


if __name__ == "__main__":
    main()

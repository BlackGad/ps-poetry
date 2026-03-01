from ps.plugin.sdk.helpers.toml import parse_project
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    f = Path(tmp) / 'pyproject.toml'
    f.write_text('[project]\nname = "test"\nversion = "1.0"')

    p = parse_project(f)

    assert p is not None, "parse_project returned None"

    print(f'Name: {p.defined_name}')
    print(f'Name exists: {p.name.exists}')
    print(f'Name jsonpath: {p.name.jsonpath}')
    print(f'Version: {p.defined_version}')
    print(f'Version jsonpath: {p.version.jsonpath}')

    # Test setting a new value
    p.name.set("new-name")
    print(f'Name after set: {p.defined_name}')

    print('Success!')

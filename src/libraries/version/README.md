# Overview

PS Version is a Python library for parsing, comparing, and formatting version numbers across multiple versioning standards. It provides a unified `Version` dataclass that automatically detects the version format, parses version strings into a consistent internal representation, and supports standard comparison operators and cross-format output.

The library supports PEP 440, SemVer, NuGet, CalVer, and loose version formats without requiring the caller to specify the format explicitly.

# Installation

```bash
pip install ps-version
```

Or with Poetry:

```bash
poetry add ps-version
```

# Quick Start

```python
from ps.version import Version, VersionStandard

version = Version.parse("1.2.3-alpha.1+build.42")
print(version.major)    # 1
print(version.minor)    # 2
print(version.patch)    # 3

v1 = Version.parse("1.2.3")
v2 = Version.parse("1.2.4")
print(v1 < v2)   # True

print(version.format(VersionStandard.PEP440))  # 1.2.3a1+build.42  (canonical PEP 440 form; 'alpha' is also accepted but 'a' is canonical)
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-version/basic_usage_example.py)

# Parsing Version Strings

Use `Version.parse()` to convert a version string into a `Version` object. The method returns `None` if no parser can match the string, so callers should handle that case.

```python
from ps.version import Version

version = Version.parse("1.2.3-rc.1+build.123")
if version is None:
    print("Could not parse version")
```

The parser tries formats in this order: PEP 440, SemVer, NuGet, CalVer, Loose. The first successful match is returned. Because several versioning standards overlap syntactically, the parser order determines which format interpretation is selected.

# Version Components

`Version` is a dataclass with the following fields. Only `major` is required; all others are optional.

```python
from ps.version import Version

version = Version.parse("1.2.3.4.post4.dev1+git.abc")
print(version.major)    # 1
print(version.minor)    # 2
print(version.patch)    # 3
print(version.rev)      # 4  (fourth numeric component)
print(version.post)     # 4  (PEP 440 post-release)
print(version.dev)      # 1  (PEP 440 dev release)
print(version.core)     # "1.2.3.4"  (numeric components as string)
```

The `core` property represents the numeric portion of the version and omits a trailing revision of zero as a convenience representation. This is a library-specific behavior, not a rule from any versioning specification.

## Pre-release

Pre-release information is represented by a `VersionPreRelease` object with a `name` (str) and optional `number` (int):

```python
version = Version.parse("1.2.3-alpha.1")
print(version.pre.name)    # alpha
print(version.pre.number)  # 1
```

## Build Metadata

Build metadata is represented by a `VersionMetadata` object. Access the full string via `str()` or individual dot-separated parts via `.parts`:

```python
version = Version.parse("1.2.3+g1234567.dirty")
print(str(version.metadata))       # g1234567.dirty
print(version.metadata.parts[0])   # g1234567
print(version.metadata.parts[1])   # dirty
```

# Comparing Versions

`Version` supports all standard comparison operators (`<`, `<=`, `==`, `!=`, `>=`, `>`). Version comparison uses PEP 440 precedence rules as the canonical ordering model across all supported version formats: dev releases come before the base release, pre-releases come before the final release, and post releases come after.

```python
from ps.version import Version

v1 = Version.parse("1.2.3a1")
v2 = Version.parse("1.2.3")
v3 = Version.parse("1.2.3.post1")

print(v1 < v2 < v3)  # True
```

# Formatting Versions

Use `Version.format(standard)` to produce a version string in a specific format. `str(version)` formats the version using the first compatible standard from the version's detected compatibility list.

```python
from ps.version import Version, VersionStandard

version = Version.parse("1.2.3-alpha.1")
print(version.format(VersionStandard.PEP440))  # 1.2.3a1
print(version.format(VersionStandard.SEMVER))  # 1.2.3-alpha.1
print(version.format(VersionStandard.NUGET))   # 1.2.3-alpha.1
```

To determine which standards a version is compatible with, use the `standards` property:

```python
version = Version.parse("1.2.3")
print(version.standards)  # [SEMVER, NUGET, LOOSE, PEP440]

version = Version.parse("1.2.3.post4")
print(version.standards)  # [PEP440]
```

# Version Constraints

Use `Version.get_constraint(constraint)` to generate a dependency constraint string from a version and a `VersionConstraint` mode.

```python
from ps.version import Version, VersionConstraint

version = Version.parse("1.2.3")
print(version.get_constraint(VersionConstraint.EXACT))            # ==1.2.3
print(version.get_constraint(VersionConstraint.MINIMUM_ONLY))     # >=1.2.3
print(version.get_constraint(VersionConstraint.RANGE_NEXT_MAJOR)) # >=1.2.3,<2.0.0
print(version.get_constraint(VersionConstraint.RANGE_NEXT_MINOR)) # >=1.2.3,<1.3.0
print(version.get_constraint(VersionConstraint.RANGE_NEXT_PATCH)) # >=1.2.3,<1.2.4
print(version.get_constraint(VersionConstraint.COMPATIBLE))       # >=1.2.3,<2.0.0
```

[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/ps-version/version_constraint_example.py)

The `COMPATIBLE` mode pins to the next breaking boundary: next major when `major > 0`, next minor when `minor > 0`, otherwise next patch.

# Using Parsers Directly

Each format has a dedicated parser class that can be used independently when the format is known in advance:

```python
from ps.version import PEP440Parser, SemVerParser, NuGetParser, CalVerParser, LooseParser

pep_parser = PEP440Parser()
version = pep_parser.parse("1.2.3a1+build")

semver_parser = SemVerParser()
version = semver_parser.parse("1.2.3-alpha.1+build.123")
```

Each parser returns `None` if the input does not match its format, making them safe to call without try/except.

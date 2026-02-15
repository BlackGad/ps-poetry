# PS Version

A Python library for parsing, comparing, and formatting software version numbers across multiple versioning standards.

The PS Version library provides a unified interface for working with version numbers from different ecosystems. It automatically detects version formats, parses them into a consistent internal representation, and supports comparisons and formatting according to various standards.

## Overview

PS Version provides:

* **Multi-standard parsing** — Automatic detection and parsing of PEP 440, SemVer, NuGet, CalVer, and loose formats
* **Version comparison** — Standardized comparison following PEP 440 rules
* **Flexible formatting** — Convert between different version standards
* **Component access** — Extract major, minor, patch, pre-release, metadata, and more
* **Type-safe** — Dataclass-based with validation
* **Zero dependencies** — Lightweight and fast

**Supported Version Standards:**

* **PEP 440** — Python packaging standard
* **SemVer** — Semantic Versioning (2.0.0)
* **NuGet** — .NET package versioning
* **CalVer** — Calendar-based versioning
* **Loose** — Flexible fallback parser

---

## Installation

```bash
pip install ps-version
```

Or with Poetry:

```bash
poetry add ps-version
```

---

## Quick Start

### Basic Usage

```python
from ps.version import Version

# Parse a version string
version = Version.parse("1.2.3")
print(version.major)  # 1
print(version.minor)  # 2
print(version.patch)  # 3
```

### Comparing Versions

```python
from ps.version import Version

v1 = Version.parse("1.2.3")
v2 = Version.parse("1.2.4")

print(v1 < v2)   # True
print(v1 == v2)  # False
```

### Formatting Versions

```python
from ps.version import Version, VersionStandard

version = Version.parse("1.2.3-alpha.1")
print(version.format(VersionStandard.PEP440))  # 1.2.3a1
print(version.format(VersionStandard.SEMVER))  # 1.2.3-alpha.1
```

---

## Core Concepts

### Version Model

All versions are represented by a single `Version` class with optional components:

* **Core numbers**: major, minor, patch, and optionally a fourth component (rev)
* **Pre-release**: Labels like "alpha", "beta", "rc" with optional numbers
* **Post-release**: PEP 440 post-release numbers
* **Dev release**: PEP 440 development release numbers  
* **Metadata**: Build information like commit hashes

```python
from ps.version import Version

# Simple version
version = Version.parse("1.2.3")

# Complex version with all components
version = Version.parse("1.2.3.post4+g1234567.dirty")
```

Only the `major` component is required; all others are optional and adapt to the version standard you're using.

### Automatic Format Detection

No need to specify the format—the library detects it automatically when parsing:

```python
Version.parse("1.2.3a1")           # Detects PEP440
Version.parse("1.2.3-alpha.1")     # Detects SemVer
Version.parse("1.2.3-beta1")       # Detects NuGet
Version.parse("2024.2.15")         # Detects CalVer
```

### Compatible Standards

Each version automatically determines which standards it's compatible with based on its components. The `standards` property returns a list of compatible formats:

```python
from ps.version import Version, VersionStandard

# Simple version is compatible with multiple standards
version = Version.parse("1.2.3")
print(version.standards)  # [SEMVER, NUGET, LOOSE, PEP440]

# Complex versions may only be compatible with specific standards
version = Version.parse("1.2.3.post4")
print(version.standards)  # [PEP440] (post-release only in PEP440)
```

---

## Parsing

Use `Version.parse()` to convert version strings into `Version` objects. The method returns `None` if parsing fails.

```python
from ps.version import Version

# Successful parsing
version = Version.parse("1.2.3-rc.1+build.123")
print(version.major)  # 1

# Failed parsing
result = Version.parse("invalid")
print(result)  # None
```

The parser automatically tries different formats in this order: PEP 440, SemVer, NuGet, CalVer, and finally a loose fallback parser.

---

## Version Components

### Core Numbers

Access the numeric parts of a version:

```python
version = Version.parse("1.2.3.4")
version.major  # 1
version.minor  # 2
version.patch  # 3
version.rev    # 4 (fourth component, optional)
version.core   # "1.2.3.4" (as string)
```

The `core` property omits trailing zeros in the revision number.

### Pre-release

Pre-release versions (alpha, beta, rc) come before the final release:

```python
version = Version.parse("1.2.3-alpha.1")
version.pre.name    # "alpha"
version.pre.number  # 1
```

### Metadata

Build metadata like commit hashes or build numbers:

```python
version = Version.parse("1.2.3+g1234567.dirty")
str(version.metadata)       # Full: "g1234567.dirty"
version.metadata.parts[0]   # First part: "g1234567"
version.metadata.parts[1]   # Second part: "dirty"
```

### PEP 440 Specific

Python-specific version components:

```python
version = Version.parse("1.2.3.post4.dev1")
version.post  # 4 (post-release number)
version.dev   # 1 (development release number)
```

---

## Formatting

Convert versions between different standards using the `format()` method:

```python
from ps.version import Version, VersionStandard

version = Version.parse("1.2.3-alpha.1")  # Parsed as SemVer

# Convert to different formats
version.format(VersionStandard.PEP440)  # "1.2.3a1"
version.format(VersionStandard.SEMVER)  # "1.2.3-alpha.1"
version.format(VersionStandard.NUGET)   # "1.2.3-alpha.1"
```

### String Conversion

Converting to string uses the first compatible standard, or PEP440 as a fallback:

```python
version = Version.parse("1.2.3")
print(str(version))  # "1.2.3" (uses SEMVER format, first compatible)

version = Version.parse("1.2.3.post4")
print(str(version))  # "1.2.3.post4" (uses PEP440, only compatible format)
```

### Standard-Specific Formatting

Each standard has its own formatting rules:

**PEP 440** (Python):

* Pre-release: `1.2.3a1` (no separator)
* Post-release: `1.2.3.post4`
* Dev release: `1.2.3.dev1`
* Metadata: `1.2.3+g1234567`

**SemVer** (JavaScript, Go):

* Pre-release: `1.2.3-alpha.1` (hyphen separator)
* Metadata: `1.2.3+build.123`
* No support for post/dev releases

**NuGet** (.NET):

* Four components: `1.2.3.4`
* Pre-release: `1.2.3-beta.1`
* No metadata support

**CalVer/Loose**:

* Simple format: `2024.2.15`
* Metadata with hyphen: `1.2.3-custom`

```python
# Example: Format the same version different ways
from ps.version import Version, VersionPreRelease, VersionStandard

version = Version(major=1, minor=2, patch=3, pre=VersionPreRelease("alpha", 1))

version.format(VersionStandard.PEP440)  # "1.2.3a1"
version.format(VersionStandard.SEMVER)  # "1.2.3-alpha.1"
version.format(VersionStandard.NUGET)   # "1.2.3-alpha.1"

# Check which standards this version is compatible with
print(version.standards)  # [SEMVER, NUGET, PEP440]
```

---

## Comparison

Versions can be compared using standard Python operators (`<`, `>`, `<=`, `>=`, `==`, `!=`).

### Comparison Rules

Versions are ordered following PEP 440 principles:

1. Core numbers are compared first (major, minor, patch, rev)
2. Development releases come before everything else
3. Pre-releases come before the final release
4. Post-releases come after the final release

```python
from ps.version import Version

# Core version comparison
Version.parse("1.0.0") < Version.parse("1.0.1")  # True
Version.parse("1.0.0") < Version.parse("2.0.0")  # True

# Pre-release vs release
Version.parse("1.0.0a1") < Version.parse("1.0.0")  # True

# Pre-release ordering
Version.parse("1.0.0a1") < Version.parse("1.0.0b1")  # True (alpha < beta)
```

**Pre-release names are case-insensitive:**

```python
Version.parse("1.0.0-Alpha.1") == Version.parse("1.0.0-alpha.1")  # True
```

---

## Version Standards

The library supports multiple version formats, each with different capabilities:

| Feature             | PEP 440 | SemVer | NuGet | CalVer | Loose |
|---------------------|---------|--------|-------|--------|-------|
| Three components    | ✓       | ✓      | ✓     | ✓      | ✓     |
| Fourth component    | ✓       | ✗      | ✓     | ✗      | ✓     |
| Pre-release         | ✓       | ✓      | ✓     | ✗      | ✗     |
| Post-release        | ✓       | ✗      | ✗     | ✗      | ✗     |
| Dev release         | ✓       | ✗      | ✗     | ✗      | ✗     |
| Metadata            | ✓       | ✓      | ✗     | ✓      | ✓     |

**Use the right standard for your ecosystem:**

* **PEP 440**: Python packages (PyPI)
* **SemVer**: JavaScript (npm), Go, Rust
* **NuGet**: .NET packages
* **CalVer**: Date-based versioning
* **Loose**: Flexible parsing for custom formats

---

## API Reference

### Version Class

The main class for working with version numbers. Create versions by parsing strings or constructing directly.

**Key capabilities:**

* Parse version strings automatically
* Access version components (major, minor, patch, etc.)
* Format versions in different standards
* Compare versions using standard operators

```python
from ps.version import Version

# Parse a version
version = Version.parse("1.2.3")

# Access components
version.major  # 1
version.core   # "1.2.3"

# Format to different standards
version.format(VersionStandard.SEMVER)
```

### VersionPreRelease Class

Represents pre-release information like "alpha", "beta", or "rc". Use this to identify development versions that come before a stable release.

```python
from ps.version import VersionPreRelease

# Create pre-release
pre = VersionPreRelease(name="alpha", number=1)
print(str(pre))  # "alpha1"

# Use in version
version = Version(major=1, pre=pre)
```

### VersionMetadata Class

Stores build metadata like commit hashes or build numbers. Access the full string or individual parts separated by dots.

**Purpose:** Track build information without affecting version precedence.

```python
from ps.version import VersionMetadata

# Git commit and dirty flag
meta = VersionMetadata("g1234567.dirty")
print(str(meta))         # Full value: "g1234567.dirty"
print(meta.parts[0])     # First part: "g1234567"
print(meta.parts[1])     # Second part: "dirty"

# Build number
build_meta = VersionMetadata("build.456")
print(build_meta.parts[0])  # "build"
print(build_meta.parts[1])  # "456"
```

### VersionStandard Enum

Identifies the version format. Use this to format versions in specific standards.

**Available standards:**

* `PEP440` — Python packaging (e.g., "1.2.3a1")
* `SEMVER` — Semantic Versioning (e.g., "1.2.3-alpha.1")
* `NUGET` — .NET packages (e.g., "1.2.3-beta")
* `CALVER` — Calendar versioning (e.g., "2024.2.15")
* `LOOSE` — Flexible formats

**Determining compatible standards:**

Each version has a `standards` property that lists which formats it can be represented in:

```python
from ps.version import Version

version = Version.parse("1.2.3")
print(version.standards)  # List of compatible standards
```

---

## Error Handling

**Validation on Construction:**

All version numbers must be non-negative. Invalid values raise `ValueError`:

```python
Version(major=-1)          # ValueError: major must be non-negative
```

**Parsing Failures:**

`Version.parse()` returns `None` for invalid input instead of raising exceptions:

```python
Version.parse("")        # None
Version.parse(None)      # None  
Version.parse("invalid") # None
```

---

## Best Practices

**Always check parse results:**

```python
version = Version.parse(user_input)
if version is None:
    raise ValueError(f"Invalid version: {user_input}")
```

**Validate format for publishing:**

```python
# Ensure PEP 440 compatibility for PyPI
from ps.version import VersionStandard

version = Version.parse(user_input)
if version and VersionStandard.PEP440 in version.standards:
    return version.format(VersionStandard.PEP440)
```

**Use comparison operators directly:**

```python
if current_version >= required_version:
    print("Requirement satisfied")
```

---

## Complete Examples

### Parsing Different Formats

```python
from ps.version import Version

# The library automatically detects the format
Version.parse("1.2.3a1")              # PEP 440
Version.parse("1.2.3-alpha.1")        # SemVer
Version.parse("1.2.3-beta1")          # NuGet
Version.parse("2024.2.15")            # CalVer
```

### Version Comparison and Sorting

```python
from ps.version import Version

versions = ["1.0.0", "2.0.0a1", "1.5.0", "2.0.0"]
parsed = [Version.parse(v) for v in versions if Version.parse(v)]

# Sort versions
sorted_versions = sorted(parsed)
print([str(v) for v in sorted_versions])
# Output: ['1.0.0', '1.5.0', '2.0.0a1', '2.0.0']

# Get latest stable release
stable = [v for v in sorted_versions if not v.pre]
latest = stable[-1] if stable else None
```

### Cross-Format Conversion

```python
from ps.version import Version, VersionStandard

# Parse as one format, output as another
version = Version.parse("1.2.3-alpha.1")  # Detected as SemVer
pep440 = version.format(VersionStandard.PEP440)  # Convert to PEP 440
print(pep440)  # "1.2.3a1"
```

### Dependency Validation

```python
from ps.version import Version

def check_dependency(installed: str, required: str) -> bool:
    installed_v = Version.parse(installed)
    required_v = Version.parse(required)
    return installed_v and required_v and installed_v >= required_v

if check_dependency("1.2.5", "1.2.0"):
    print("Dependency satisfied")
```

### Build Version with Metadata

```python
from ps.version import Version, VersionMetadata, VersionStandard

def create_build_version(base: str, commit: str, build_num: int) -> str:
    base_v = Version.parse(base)
    if not base_v:
        raise ValueError(f"Invalid version: {base}")
    
    build_version = Version(
        major=base_v.major,
        minor=base_v.minor,
        patch=base_v.patch,
        post=build_num,
        metadata=VersionMetadata(f"g{commit[:7]}")
    )
    return build_version.format(VersionStandard.PEP440)

version = create_build_version("1.2.3", "abc123def", 42)
print(version)  # "1.2.3.post42+gabc123d"
```

### Version Range Check

```python
from ps.version import Version

def is_compatible(version: str, min_v: str, max_v: str) -> bool:
    v = Version.parse(version)
    min_ver = Version.parse(min_v)
    max_ver = Version.parse(max_v)
    
    return all([v, min_ver, max_ver]) and min_ver <= v < max_ver

if is_compatible("1.5.0", "1.0.0", "2.0.0"):
    print("Version is compatible")
```

### Extracting Version Information

```python
from ps.version import Version, VersionStandard

version = Version.parse("1.2.3.post4+g1234567.dirty")

print(f"Core: {version.core}")                    # "1.2.3"
print(f"Compatible standards: {[s.value for s in version.standards]}")  # ["pep440"]
print(f"Post-release: {version.post}")            # 4
print(f"Commit: {version.metadata.parts[0] if version.metadata else 'N/A'}")  # "g1234567"
print(f"Dirty: {version.metadata.parts[1] if version.metadata else 'N/A'}")  # "dirty"
```

---

## Summary

PS Version is a unified library for working with software version numbers across multiple ecosystems.

**What it does:**

* Automatically detects and parses version formats
* Compares versions using standardized rules
* Converts between different version standards
* Extracts version components and metadata
* Validates version numbers

**Why use it:**

* **Universal** — Works with Python, JavaScript, .NET, and custom formats
* **Simple** — Automatic format detection, no configuration needed
* **Reliable** — Follows established standards (PEP 440, SemVer, NuGet)
* **Lightweight** — No dependencies
* **Type-safe** — Built with Python dataclasses

**Perfect for:**

* Package managers and build tools
* Dependency validation
* CI/CD pipelines
* Release automation
* Cross-platform tooling

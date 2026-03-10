---
name: documentation
description: 'Create, update, review, or fix documentation files (.md), README files, code examples, example files in examples/ directory. Use when writing component docs, updating README, managing examples, adding GitHub example links, or validating documentation structure.'
---

# Documentation Management

## Workflow

1. **Identify target**: Locate `pyproject.toml` to determine which component's README to update
2. **Analyze codebase**: Review source files in `plugin/src/`, `sdk/src/`, `modules/*/src/`, `libraries/*/src/`, test files in each component's `tests/`, and experiment files in `experiments/` for usage patterns
3. **Update README.md**: Modify ONLY the component's `README.md` file (no other files)
4. **Manage examples**: Create/update/delete example files in `examples/<package_name>/`
5. **Validate**: Check markdown linting and ruff linting for example files
6. **Complete**: Ensure all mandatory requirements are met

Also invoke the [linting skill](./../linting/SKILL.md) when creating or modifying example Python files.

## Mandatory Requirements Checklist

Before marking work complete, verify ALL of these:

* [ ] `# Overview` section present at top of README.md
* [ ] `# Installation` section present after Overview with pip/poetry installation commands
* [ ] `# Quick Start` section present after Installation with minimal working example
* [ ] Every code example has a corresponding file in `examples/<package_name>/`
* [ ] Every example file is referenced in documentation (unreferenced files deleted)
* [ ] Each example includes GitHub link: `https://github.com/BlackGad/ps-poetry/blob/main/src/examples/<package_name>/<file>.py`
* [ ] All example files are self-contained (no imports from other example files)
* [ ] All example files pass ruff linting (zero errors)
* [ ] Markdown linting checked via VS Code Problems panel (zero errors)
* [ ] No private methods/types (prefixed with `_`) documented
* [ ] No prohibited sections (Requirements, Testing methodology, etc.)
* [ ] Using `*` for bullet lists in README files (not `-`)
* [ ] No `---` horizontal separators between sections

## Example Files Rules

### File Creation and Management

**Location**: `examples/<package_name>/` from workspace root

**Naming**: `<feature>_example.py` (e.g., `basic_usage_example.py`, `version_parsing_example.py`)

**Structure**:

* One example per file (no multi-example files)
* Self-contained: all imports, types, and code included
* No cross-file imports: examples must NOT import from other example files
* Fully executable: no placeholders or incomplete code
* Must pass ruff linting before completion

**Recommended Python example template**:

```python
from ps.<package>.<module> import <SomeClass>


def main() -> None:
    # Demonstrate operation(s) using the package API.
    ...


if __name__ == "__main__":
    main()
```

**Synchronization**:

* Every example in docs -> Must have example file
* Every example file -> Must be referenced in docs
* Unreferenced files -> DELETE immediately

### Linking Examples in Documentation

**Required format**: Include this link for every example

```markdown
[View full example](https://github.com/BlackGad/ps-poetry/blob/main/src/examples/<package_name>/<file>.py)
```

**Presentation strategy**:

* **Short examples** (< 20 total lines including blank lines and comments): Inline code in docs + maintain in file
* **Long examples** (>= 20 total lines): Show link + explanation, keep full code in file only
* **Inline snippet style**: Show the core operation being demonstrated without wrapper boilerplate
* **Inline snippet scope**: Do not include `main()` wrappers in README snippets

## Content Writing Standards

### Language and Style

* Use professional technical writing style without informal language or first-person pronouns
* Focus on usage and integration from the perspective of developers consuming the component
* Use specific, action-oriented section headings that describe the content (e.g., "Parse Version Strings", "Resolve Token Expressions")
* Organize content into distinct sections with focused topics rather than combining multiple concepts in single paragraphs
* Include at least one descriptive paragraph per section; do not leave sections with only a header and a code block
* Do not use numbered section headers (e.g., avoid "1. Introduction", "2. Usage")

### Code in Documentation

* Show practical, executable code examples only
* Validate all code against the current implementation in source files
* Reference files in `experiments/` to identify real-world usage patterns
* Exclude private methods/types (those prefixed with `_`) from all documentation
* Docstrings: public APIs only (match main codebase style as defined in AGENTS.md)
* Keep full example code in files under `examples/<package_name>/`, linked from the README
* README files should contain code hints demonstrating usage patterns, not full executable examples (full examples belong in `examples/<package_name>/` files)
* Include code snippets demonstrating usage when meaningful and not excessively large
* When documenting optional parameters in parameter lists, use human-readable format like "(optional)" or "(str, optional)" instead of Python-specific syntax like "str | None" or "Optional[str]"

### Document Structure

Start with `# Overview` directly, then organize into clear sections with descriptive headings.

**Example structure**:

```markdown
# Overview

2-4 paragraph introduction explaining the component's purpose, primary use cases, and key capabilities...

# Installation

Exact package installation instructions with pip and poetry commands...

# Quick Start

Single, executable code example (10-30 lines) showing one core operation...

# Key Features

Detailed feature explanations with code examples...

# Advanced Usage

More complex scenarios and configurations...
```

### Prohibited Content

**Do NOT include**:

* Requirements sections
* Testing methodology sections
* Implementation details not relevant to users
* Private types/methods (prefixed with `_`)

## Formatting Rules

**Required in README files**:

* Use `*` for bullet points (never `-`)
* Maintain consistent markdown formatting
* Include GitHub links for all examples

**Prohibited**:

* Horizontal separators (`---`) between sections
* Numbered section headers
* Mixed bullet point styles
* Backticks in section headers (e.g., `# \`SomeClass\`` or `## \`method_name\``)

## Validation Process

### Markdown Linting

**MANDATORY**: Check VS Code Problems panel before completion

**Action**: Fix all markdown linting warnings and errors

**Note**: Markdown lint rules are configured in `.markdownlint.json`

**Important**: Use VS Code Problems panel, NOT ruff/Python linters for markdown files

### Python Linting (Example Files)

**MANDATORY**: All example files must pass:

```bash
poetry run ruff check examples/<package_name>/
```

**Requirement**: Zero errors before completion

## Quick Reference

| Task | Action |
| ---- | ------ |
| Create example | Add to `examples/<package_name>/` + link in README |
| Update example | Modify file + sync with README inline code |
| Delete example | Remove file if NOT referenced in README |
| Long example | Link only + explanation |
| Short example | Inline snippet (no `main()`) + maintain full file |
| Validate markdown | Check VS Code Problems panel |
| Validate Python | Run `poetry run ruff check` |

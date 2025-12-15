# Documentation Guidelines

When working on documentation, follow these instructions alongside **AGENTS.md**.

## Cross-Reference Requirements

- When documentation changes impact tests, consult **AGENTS_TESTS.md**
- When documentation contains code snippets, validate them using **AGENTS_LINTING.md**

## Scope and Process

### Project Organization

- All project documentation resides in the `documentation/` folder
- Plugin implementation is located in `plugin/src/ps/plugin/core/`
- Extension modules will be placed in `modules/` folder
- Analyze source files and tests for accurate documentation

## Content Standards

### Writing Requirements

- Use formal and neutral language throughout
- Focus on client-facing usage patterns and examples
- Preserve all existing correct content
- Ensure all code snippets are functional and tested

### Code Documentation

- Exclude private types and methods (prefixed with `_`)
- Provide practical, working examples
- Validate all code snippets against current implementation
- Use plugin functionality to provide proper code hints and usage patterns in examples

### Structure Guidelines

- Organize content into multiple logical sections
- Avoid creating a single main paragraph structure
- Use clear, descriptive section headings

## Content Restrictions

### Prohibited Sections

- Requirements or installation sections
- Testing methodology sections
- Unrelated or tangential material
- Web-specific code references

### Formatting Restrictions

- Do not use `---` separators between sections
- Maintain consistent markdown formatting throughout

## Document Template

```md
# Section One

Content for the first logical section...

# Section Two

Content for the second logical section...

# Additional Sections

Continue with additional sections as needed...
```

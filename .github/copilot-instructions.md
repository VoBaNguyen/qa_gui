# Python Code Conventions

This document outlines the common code conventions that all contributors, especially senior developers, should follow in this project.

## General Guidelines

- **Follow [PEP 8](https://pep8.org/)** for code style and formatting.
- Use **meaningful variable, function, and class names**.
- Write **modular, reusable, and testable code**.
- Keep functions and methods **short and focused** (ideally < 20 lines).
- Avoid code duplication; use helper functions or classes where appropriate.

## Imports

- Group imports in the following order: standard library, third-party, local modules.
- Use absolute imports where possible.
- Each import should be on a separate line.

## Type Annotations

- Use **type hints** for all function arguments and return values.
- Use `Optional`, `List`, `Dict`, etc., from `typing` as needed.

## Documentation

- Write **docstrings** for all public modules, classes, and functions using [PEP 257](https://www.python.org/dev/peps/pep-0257/) conventions.
- Use comments to explain complex logic, but avoid obvious comments.

## Error Handling

- Use **exceptions** for error handling, not return codes.
- Catch only specific exceptions; avoid bare `except:` blocks.
- Log errors where appropriate.

## Testing

- Write **unit tests** for all new features and bug fixes.
- Use descriptive test names and keep tests isolated.
- Place tests in a `tests/` directory.

## Code Reviews

- All code must be reviewed before merging.
- Address all review comments and suggestions.

## Formatting Tools

- Use **Black** for code formatting.
- Use **isort** for import sorting.
- Use **flake8** or **pylint** for linting.

## Miscellaneous

- Avoid hardcoding values; use constants or configuration files.
- Remove unused code and imports.
- Ensure code is compatible with the supported Python version(s).

---
Adhering to these conventions ensures code quality, readability, and maintainability for all contributors.
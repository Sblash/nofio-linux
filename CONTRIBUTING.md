# Contributing to nofio-linux

Thank you for your interest in contributing to the nofio-linux project! This document outlines the guidelines and standards for contributions.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Include detailed information about your hardware, OS, and steps to reproduce
- Check existing issues before creating new ones

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run any existing tests (when available)
5. Commit your changes with descriptive commit messages
6. Push to your fork and submit a pull request

### Pull Request Guidelines

- Follow the existing code style
- Keep commits atomic and well-described
- Include tests when adding new functionality
- Update documentation when making significant changes
- Reference any related issues in the PR description

## Coding Standards

### Technology Stack

| Component | Language | Build |
|-----------|----------|-------|
| Utility app | Dart | Flutter |
| SteamVR driver | C++ | CMake |
| Firmware analysis | Python 3 | Standalone scripts |

### General

- Use consistent indentation
- Follow the existing naming conventions
- Use descriptive variable and function names
- Comment complex logic
- Keep functions focused and single-purpose

## Documentation Standards

- Use Markdown format
- Keep documentation up-to-date with code changes
- Use clear and concise language
- Include code examples when helpful

### Discovery Documentation Rule

Every discovery must be documented in a markdown file within the relevant folder. For example, if you are working on the utility app, add a markdown file in the "utility" folder. The documentation must specify:
- Which **phase** it belongs to (Phase 0, Phase 1, Phase 2, Phase 3, or Phase 4)
- The **topic** or subject of the discovery

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(driver): add initial SteamVR driver skeleton

Implements HmdDriverFactory with basic device registration.
Closes #123
```

## License

By contributing to this project, you agree that your contributions will be licensed under the same GNU General Public License v3.0 (GPLv3) as the rest of the project.

## Code of Conduct

- Be respectful and inclusive
- Keep discussions technical and constructive
- No harassment or offensive behavior will be tolerated
- Follow GitHub's Community Guidelines

## Getting Help

- For usage questions, see the documentation
- For development questions, open an issue or discussion

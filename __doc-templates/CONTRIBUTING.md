# Contributing to {{PROJECT_NAME}}

First off — thank you for taking the time to contribute! 🎉  
Every contribution, no matter how small, makes a difference.

This document outlines the process and standards for contributing to **{{PROJECT_NAME}}**.  
Please read it fully before opening a pull request or issue.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Development Setup](#development-setup)
- [Branch Naming Convention](#branch-naming-convention)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](./CODE_OF_CONDUCT.md).  
By participating, you are expected to uphold this code.  
Report unacceptable behavior to **{{CONTACT_EMAIL}}**.

---

## How Can I Contribute?

### Reporting Bugs

Before reporting, please:

1. Check the [existing issues](https://github.com/{{USERNAME}}/{{REPO_NAME}}/issues) to avoid duplicates.
2. Make sure you are using the latest version.

When filing a bug report, include:

- **Summary** — A clear, one-line description of the bug.
- **Steps to Reproduce** — Numbered, minimal reproduction steps.
- **Expected Behavior** — What you expected to happen.
- **Actual Behavior** — What actually happened.
- **Environment** — OS, runtime version, project version.
- **Screenshots / Logs** — If applicable.

> Use the [Bug Report template](https://github.com/{{USERNAME}}/{{REPO_NAME}}/issues/new?template=bug_report.md) when available.

---

### Suggesting Features

Feature suggestions are welcome! Please:

1. Check the [Roadmap](../README.md#roadmap) and open issues first.
2. Open a new issue using the **Feature Request** template.
3. Describe the problem the feature solves, not just the solution.

---

### Submitting Pull Requests

1. Fork the repository.
2. Create a new branch following the [Branch Naming Convention](#branch-naming-convention).
3. Make your changes with clear, focused commits.
4. Ensure all tests pass.
5. Open a pull request against the `{{BASE_BRANCH}}` branch (usually `main` or `develop`).
6. Fill out the pull request template completely.

> PRs that do not follow the guidelines may be closed without review.

---

## Development Setup

```bash
# 1. Fork and clone your fork
git clone https://github.com/{{YOUR_USERNAME}}/{{REPO_NAME}}.git
cd {{REPO_NAME}}

# 2. Add the upstream remote
git remote add upstream https://github.com/{{USERNAME}}/{{REPO_NAME}}.git

# 3. Install dependencies
{{DEPENDENCY_INSTALL_COMMAND}}

# 4. Create your feature branch
git checkout -b feature/your-feature-name

# 5. Run in development mode
{{DEV_RUN_COMMAND}}
```

---

## Branch Naming Convention

Use the following prefixes when creating branches:

| Prefix | Use For |
|---|---|
| `feature/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation updates |
| `refactor/` | Code restructuring (no behavior change) |
| `test/` | Adding or updating tests |
| `chore/` | Build, tooling, or dependency updates |

**Examples:**

```
feature/user-authentication
fix/crash-on-empty-input
docs/update-api-reference
```

---

## Commit Message Convention

This project follows the **[Conventional Commits](https://www.conventionalcommits.org/)** specification.

### Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | When to Use |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting (no logic change) |
| `refactor` | Code restructuring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |

### Examples

```
feat(auth): add JWT token refresh logic

fix(ui): resolve button overlap on mobile screen

docs(readme): update installation steps for Windows

chore(deps): bump axios from 1.2.0 to 1.4.0
```

---

## Pull Request Guidelines

Before submitting your PR, make sure:

- [ ] Code follows the project's [code style](#code-style)
- [ ] All existing tests pass
- [ ] New tests are added for new functionality
- [ ] Documentation is updated if needed
- [ ] The PR title follows the commit message convention
- [ ] The PR description clearly explains the **what** and **why**
- [ ] You've linked the related issue (e.g., `Closes #42`)

---

## Code Style

<!-- Customize this section for your stack -->

This project uses **{{LINTER/FORMATTER}}** to enforce consistent code style.

```bash
# Run linter
{{LINT_COMMAND}}

# Auto-fix formatting
{{FORMAT_COMMAND}}
```

Key style rules:
- {{Rule 1, e.g. "Use 2-space indentation"}}
- {{Rule 2, e.g. "Prefer const over let where possible"}}
- {{Rule 3, e.g. "Always add JSDoc comments to exported functions"}}

---

## Testing

```bash
# Run all tests
{{TEST_COMMAND}}

# Run tests in watch mode
{{TEST_WATCH_COMMAND}}

# Run with coverage
{{TEST_COVERAGE_COMMAND}}
```

> All PRs must maintain or improve the existing test coverage threshold of **{{COVERAGE_THRESHOLD}}%**.

---

Thank you again for contributing to **{{PROJECT_NAME}}**! 🙏

© {{YEAR}} {{AUTHOR_OR_ORGANIZATION}}

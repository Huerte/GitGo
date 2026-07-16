# Contributing to GitGo

Thanks for considering a contribution. This guide covers everything you need to go from zero to a submitted pull request.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Making Changes](#making-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Good First Issues](#good-first-issues)

---

## Code of Conduct

Be direct, be respectful. No gatekeeping. This is a student project open to everyone, regardless of experience level. If someone is learning, help them, don't mock them.

This applies to all project spaces: GitHub issues, pull requests, and any public discussion tied to this repository. It covers contributors and maintainers alike, including first-time contributors.

To report a violation, contact the maintainer at [Report a Violation](mailto:huertejerald@gmail.com?subject=GitGo%20CoC%20Report).
A short description of what happened is enough.

Violations may result in a warning, removal of the offending content, or a block from the repository depending on severity.

---

## Getting Started

### Prerequisites

- Python 3.8+
- Git 2.x+

### Fork and Clone

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/GitGo.git
cd GitGo

# 2. Add the upstream remote so you can pull future changes
git remote add upstream https://github.com/Huerte/GitGo.git
```

### Set Up the Dev Environment

```bash
# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify the install worked
gitgo -r
```

That's it. No Docker, no virtual environment required

---

## Project Structure

```
src/pygitgo/
├── main.py                # Entry point, argument parsing, command routing
├── exceptions.py          # GitGoError hierarchy (GitCommandError)
├── commands/
│   ├── config.py          # gitgo config handler (set/get defaults)
│   ├── git_branch.py      # Branch queries: get current branch, check existence, create
│   ├── git_core.py        # Core write operations: commit, init, push
│   ├── git_remote.py      # Remote sync, rebase recovery, connection checks
│   ├── init.py            # gitgo init handler (local project scaffolding)
│   ├── jump.py            # Safe branch switching with Try-and-Revert engine
│   ├── link.py            # Init, link remote, and push a new repo
│   ├── log.py             # gitgo log handler (commit history)
│   ├── new.py             # gitgo new handler (quickstart: init + repo + link)
│   ├── pull.py            # Safe pull with auto-stash and rebase
│   ├── push.py            # Stage, commit, push (with selective staging support)
│   ├── repo.py            # gitgo repo handler (remote GitHub repo creation)
│   ├── resolve.py         # gitgo resolve handler (conflict resolution)
│   ├── staging.py         # Interactive file picker for selective commits
│   ├── stash.py           # Low-level git stash wrappers (push/pop/apply/drop/list/clear)
│   ├── state.py           # Named stash interface (save/load/delete/list)
│   ├── undo.py            # Undo commit, undo add, wipe changes
│   └── user.py            # gitgo user handler (login/logout/display)
├── auth/
│   ├── account.py         # Git identity (user.name / user.email)
│   ├── manager.py         # Login/logout orchestration
│   └── ssh_utils.py       # SSH key generation, known_hosts, HTTPS to SSH conversion
└── utils/
    ├── bootstrap.py       # First-run setup (git check, known_hosts init)
    ├── cli_io.py          # CLI output and interactive prompts
    ├── colors.py          # ANSI color helpers (info, success, warning, error)
    ├── config.py          # GitGo config read/write via git config --global
    ├── executor.py        # subprocess wrapper with spinner
    ├── platform.py        # OS/Termux detection (get_platform, is_termux)
    ├── update_checker.py  # Background PyPI version check
    └── validators.py      # URL validation helpers (validate_repo_url)
```

**Key rules:**
- Command logic lives in `commands/`. Each file owns one domain. `main.py` only parses args and routes.
- Utils are pure helpers with no side effects. If a function prints or raises, it belongs in `commands/`, not `utils/`.
- Entry points follow the `*_operation` naming pattern: `push_operation`, `state_operation`, `user_operation`, etc.

---

## Running Tests

```bash
# Run the full test suite
pytest tests/ -v

# Run a single test file
pytest tests/test_jump.py -v

# Run with coverage report
pytest tests/ --cov=pygitgo --cov-report=term-missing
```

Tests use `pytest` and `pytest-mock`. No real Git repos are created during tests. Mock `subprocess.run` and `run_command` where needed.

Note: The codebase now includes tests for the CLI helpers (`tests/test_cli_io.py`) and relies on additional dev dependencies such as `yaspin` and `pick`. Ensure these are installed in your development environment (see `pyproject.toml`).

### Writing Tests

- Place new test files in `tests/` named `test_<module>.py`.
- Use the `tmp_path` fixture for any tests that need a real filesystem.
- Mock `subprocess.run` at `pygitgo.utils.executor.subprocess.run` for subprocess calls.
- Every new command should have at least a happy-path and one failure-path test.

---

## Making Changes

### Branch Naming

```
feat/short-description    # New features
fix/short-description        # Bug fixes
docs/short-description       # Documentation only
chore/short-description      # Maintenance, refactoring, CI
```

### Commit Messages

Use plain, direct English. Describe what changed and why if it's not obvious.

```bash
# Good
git commit -m "fix: prevent sys.exit in jump_operation when called from push"
git commit -m "feat: add gitgo log command with color-coded history"
git commit -m "docs: add dev setup instructions to CONTRIBUTING"

# Avoid
git commit -m "fix stuff"
git commit -m "update"
```

### Code Style

- Follow existing patterns. If the surrounding code does something a certain way, match it.
- No type annotations required, but don't make the code harder to read.
- Keep functions under 40 lines. If a function is growing, split it.
- Add a docstring if the function's purpose isn't immediately obvious from its name.

### Error Handling

- Raise `GitGoError` subclasses (`GitCommandError`) instead of calling `sys.exit()` inside command modules.
- Only `main.py` should call `sys.exit()`. Command functions should raise errors and may return a boolean success flag (`True`/`False`) to indicate operation outcome.
- Prefer raising a `GitGoError` for recoverable/user-facing failures instead of printing and returning silently.
- Never swallow exceptions silently with empty `except` blocks.

### CLI output & UX

- Centralize interactive and formatted CLI output through `pygitgo.utils.cli_io`.
- Use the helpers: `info`, `warning`, `error`, `success`, `confirm`, `danger`, and `banner` for consistent prompts and messaging.
- Avoid using `pygitgo.utils.colors` as print wrappers; `colors.py` now only exposes ANSI constants.
- Use `confirm(..., destructive=True)` for irreversible actions so prompts clearly indicate risk.
- Command implementations should avoid raw `input()` or ad-hoc `print()`; prefer the `cli_io` helpers for testability.

---

## Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feat/your-feature
   ```

2. Open a Pull Request against `Huerte/GitGo:main`.

3. Fill in the PR template. It has six sections: Type, Overview, Changes, Breaking Changes, How to Test, and Checklist. If you are unsure how to fill it in, see the template itself for guidance or open an issue and ask.

4. The CI pipeline will run `pytest` automatically. Make sure it passes before requesting a review.

5. If your PR adds a new command, update `README.md` with the usage example and command reference entry.

---

## Good First Issues

Not sure where to start? The table below lists tasks sized for a first contribution. Each one is self-contained and has a clear scope.

Before picking one, clone the repo and read through the [Project Structure](#project-structure) section so you know where things live.

| Task | Difficulty | Where to start | What to do |
|------|------------|----------------|------------|
| `gitgo amend` | ⭐ | New command file | Wrap `git commit --amend -m "<message>"`. Add a confirmation prompt before it runs, because amend rewrites history, so the user should opt in. |
| `gitgo diff` | ⭐ | New command file | Wrap `git diff` and `git diff --staged`. Add a `-s` / `--staged` flag to toggle between unstaged and staged output. |
| GitLab & Bitbucket SSH | ⭐⭐ | `auth/ssh_utils.py` | The host regex only matches `github.com`. Extend it to cover `gitlab.com` and `bitbucket.org`. |
| `gitgo status` | ⭐⭐ | New command file | Parse `git status --porcelain` and display staged, unstaged, and untracked files in labeled groups. Handle renamed files and merge conflict markers as edge cases. |
| `gitgo branch` | ⭐⭐ | New command file | Parse `git branch -a` and list all branches with the current one highlighted. Separate local and remote branches into labeled groups. |
| Shell completions | ⭐⭐⭐ | New file | Add tab-completion for Bash, Zsh, and Fish using `argcomplete` or hand-written scripts. PowerShell is optional. |

If nothing here fits, check the [open issues](https://github.com/Huerte/GitGo/issues) for anything tagged `good first issue`. If you have an idea that isn't listed, open an issue first before writing code.

---

If you have a question that isn't covered here, open an issue and ask. No question is too basic.

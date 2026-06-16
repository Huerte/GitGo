# Changelog

All notable changes to GitGo are documented here.

Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.8.1] - 2026-06-16

### Changed
- **Performance:** Cached the SSH handshake response so it doesn't run twice during login.
- **UX:** Added a loading spinner to the GitHub connection check so the terminal doesn't freeze silently.
- **Performance:** Removed a redundant network check that ran the first time you used any command.
- **UX Refactoring:** Merged success and error messages with loading spinners across all commands. Success text now prints inline via `ok_text`, and failure text via `err_text`/`fail_text`, eliminating trailing blank lines and duplicate output.
- **Documentation:** Added `docs/login-guide.md`, a step-by-step login guide covering the full `gitgo user login` flow.

### Fixed
- Fixed the 4-10 second silent delay during `gitgo user login`.

---

## [1.8.0] - 2026-06-12

### Added
- **Remote Repo Creation:** Added `gitgo repo` to create a remote GitHub repository without leaving the terminal.
- **Quickstart Command:** Added `gitgo new <name> [lang]` as a one-shot command that scaffolds a local project, creates the GitHub repo, and pushes it all in sequence.

### Changed
- **Internal Utils:** Centralized browser opening logic and updated the auth manager to support repo creation tokens.
- `gitgo new` token prompt now opens the classic PAT page by default, making it easier to create non-expiring tokens.
- **Python Scaffolding:** `gitgo init <name> python` now generates a modern `pyproject.toml` and `.python-version` file instead of `requirements.txt`.
- **Template URLs:** `gitgo init --template` now supports full GitHub URLs (e.g., `https://github.com/owner/repo` or `.git` extensions) in addition to the short `owner/repo` format.
- Cleaned up old commented-out code in `manager.py`.

### Fixed
- Fixed `gitgo new` skipping the initial commit and push due to a double `git init` bug. It now properly deploys the scaffolded files.
- Fixed `gitgo new` opening the browser on every call. It now saves the token to git config (`gitgo.github-token`) after the first paste.
- Fixed `gitgo new` crashing when an old token expires. It now clears the dead token and re-prompts automatically.

---
 
## [1.7.1] - 2026-06-03

### Added
- **Expanded Undo:** Added `gitgo undo link` to cleanly remove an initialized remote and undo the initial commit, and `gitgo undo push` to force-revert the last remote push.
- **Dynamic Branch Initialization:** `gitgo link` and core init routines now dynamically resolve the default branch name. It respects your global `init.defaultBranch` setting, falls back to the `gitgo.default-branch` config, and defaults to `main` if neither is found.

### Fixed
- Fixed misleading post-action hints in `gitgo link` and `gitgo push` that incorrectly suggested `undo commit` instead of a full link/push revert.
- Fixed `gitgo pull` autostash recovery hint hardcoding the stash index to 1.

---

## [1.7.0] - 2026-06-02

### Added
- **Auto SSH Commit Signing:** GitGo now uses the SSH key generated during `gitgo user login` to automatically sign all commits using temporary `-c` flags, giving you the Verified badge on GitHub without modifying global git configs.
- **Safe Interruptions:** Hitting `Ctrl+C` (KeyboardInterrupt) mid-command now triggers smart, command-specific cleanup routines. It aborts in-progress rebases, unstages partial commits, and tells you exactly what state your files are in.

### Changed
- Removed redundant confirmation prompts during branch switches and deployments, replacing them with automatic actions and post-action undo hints for a smoother UX.
- Removed the `allow_fail` flag from `run_command` and switched to a robust `try/except` exception-based architecture to prevent silent failures.
- Refactored CLI messaging to use a consistent tone, removing robotic phrases and filler words.
- Standardized terminal output spacing and colors across all commands.
- Updated success banners to a concise, military-style format for major operations.
- Improved error messages to provide actionable next steps instead of generic advice.
- Refactored codebase to standardize internal API returns, remove redundant checks, and optimize stash operations.
- Split `git_operations.py` into `git_core.py`, `git_branch.py`, and `git_remote.py` for cleaner separation of concerns.
- Moved `config_operation` out of `utils/config.py` into `commands/config.py`.
- Moved `user_management` and `display_current_user` out of `main.py` into `commands/user.py`.
- Renamed `stash_operation.py` to `stash.py`, `platform_utils.py` to `platform.py`, and `setup.py` to `bootstrap.py`.
- Renamed all command handler entry points to a consistent `*_operation` naming pattern (`state_operation`, `undo_operation`, `user_operation`).
- Moved `validate_repo_url` out of `commands/link.py` into `utils/validators.py`.
- Removed dead code: `get_status_content()`, `create_main_branch()`, unused `from json import load` import, and 11 installer-only functions from `platform.py`.

### Fixed
- Fixed GitGo hanging indefinitely during login if an SSH passphrase prompt was triggered invisibly.
- Fixed the browser failing to open in some environments by always printing the GitHub URL as a fallback.
- Improved login failure messaging to suggest concrete fixes (like checking the SSH agent).
- Fixed `gitgo state` not parsing short-form aliases (`-l`, `-s`, `-o`, `-d`) correctly.
- Fixed chronological ordering in `gitgo state list` (now displays old to new, numbered 1, 2, 3) and accurately maps IDs to Git's internal stash index.
- Fixed `gitgo state` crashing when parsing stashes that output dates instead of indices.
- Fixed `gitgo state load` attempting to run even when no states exist.
- Fixed `gitgo state` silently accepting conflicting inputs (like `gitgo state list -s`).
- Fixed `-a / --all` flag applying to all state actions; it is now strictly locked to `delete`.
- Fixed `gitgo link` running `git add .` on existing repositories, which staged unwanted files.
- Fixed `gitgo push --select` ignoring your selection and committing everything anyway.
- Fixed `gitgo user login` crashing when an invalid email was provided or if `ssh-keygen` failed.
- Fixed `gitgo user logout` wiping git config even if SSH key deletion failed.
- Fixed `gitgo jump` running a slow network pull when creating a brand new local branch.

---

## [1.6.2] - 2026-05-29

### Fixed
- Fixed `gitgo push` stopping after a branch jump. It now completes the commit and push automatically.

---

## [1.6.1] - 2026-04-23

### Fixed
- Fixed update checker thread not terminating cleanly on Windows when `gitgo -r` is called.
- Fixed cached version file being written to the wrong path on Termux.
- Fixed incorrect version comparison when PyPI returns a pre-release tag.

---

## [1.6.0] - 2026-04-20

### Added
- **Auto-Update Checker:** Queries PyPI for newer versions using a background thread on startup. GitGo caches these results locally for 7 days.
- Update notification displays a one-line prompt: `GitGo vX.X.X is available! Run: pip install --upgrade pygitgo`.

---

## [1.5.0] - 2026-04-18

### Added
- **`gitgo push -s` / `--select`:** Adds a file picker before you commit. You select the files you want to push. GitGo offers to save files you leave unstaged to a state.

---

## [1.4.0] - 2026-03-29

### Added
- **`gitgo pull`:** Safe pull with automatic stash-before-pull and rebase strategy. Stashes uncommitted work, pulls cleanly with `--rebase`, then re-applies your changes. No accidental merge commits.

---

## [1.3.0] - 2026-03-29

### Added
- **`gitgo undo`:** Three undo targets:
  - `gitgo undo commit` : Soft-resets the last commit. Files stay untouched.
  - `gitgo undo add` : Unstages all staged files (`git reset HEAD`).
  - `gitgo undo changes` : Permanently wipes all uncommitted edits and untracked files. Prompts for confirmation before executing.

---

## [1.2.0] - 2026-03-23

### Added
- **`gitgo config`:** Persist default branch name and default commit message locally so you never have to type them on every command.
  - `gitgo config set default-branch develop`
  - `gitgo config set default-message "WIP: updates"`
  - `gitgo config get default-branch`

---

## [1.1.1] - 2026-03-23

### Fixed
- Fixed pull failing because the wrong branch name was being read from the remote.
- Fixed crash when running commands while in a detached HEAD state.

---

## [1.1.0] - 2026-03-23

### Added
- **`gitgo jump`:** Safe branch switching with the Try-and-Revert engine. Auto-stashes uncommitted work, checks out the target branch, pulls from main, and re-applies the stash. On merge conflict, offers a full revert back to the original state.
- **`gitgo state`:** Human-readable interface over `git stash`. States are named and indexed so you never have to remember cryptic stash refs.
  - `save`, `load`, `list`, `delete` subcommands.
  - Short aliases: `-s`, `-o`, `-l`, `-d`.

---

## [1.0.2] - 2026-03-21

### Fixed
- Fixed silent crash when Git is not installed. GitGo now checks on startup and shows a clear error message.
- Fixed commands exiting without explanation on failure. Errors are now handled and reported to the user.
- Fixed incorrect OS detection on macOS.
- Fixed `gitgo state load` printing raw internal data instead of the saved state name.
- Fixed `gitgo link` accepting malformed URLs. HTTPS and SSH formats are now validated before executing.

---

## [1.0.1] - 2026-03-21

### Changed
- Updated README with revised installation guide, usage examples, and command reference. No functional changes.

---

## [1.0.0] - 2026-03-21

### Added
- **`gitgo push`:** Stage all, commit, and push in one command. Detects unpushed commits and skips an empty commit if nothing new is staged.
- **`gitgo link`:** Initialize a Git repo in the current directory, set the remote, commit everything, and push. Handles already-initialized repos and pulls unrelated histories.
- **`gitgo user login`:** Generates an `ed25519` SSH key, adds it to `ssh-agent`, prints the public key, and opens `github.com/settings/ssh/new` automatically.
- **`gitgo user logout`:** Removes SSH keys and clears Git identity config.
- **`gitgo user`:** Shows current Git name and email.
- **HTTPS to SSH Conversion:** If your remote is HTTPS and SSH is configured, GitGo silently converts the remote URL before pushing.
- **Termux Support:** Detects Termux via environment variables, adjusts binary paths to `$PREFIX/bin`, uses `termux-open` for browser actions, and handles the `detected dubious ownership` Git error natively.
- **URL Validation:** `gitgo link` validates the repository URL format (HTTPS and SSH) before proceeding.
- **Exception Hierarchy:** `GitGoError`, `GitCommandError` for structured error handling across the codebase.

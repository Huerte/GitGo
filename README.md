<div align="center">

![GitGo Banner](assets/banner.png)

[![Tests](https://github.com/Huerte/GitGo/actions/workflows/tests.yml/badge.svg)](https://github.com/Huerte/GitGo/actions)
[![PyPI version](https://img.shields.io/pypi/v/pygitgo?color=blue&label=PyPI)](https://pypi.org/project/pygitgo)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pygitgo?color=blue)](https://pypi.org/project/pygitgo)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/Huerte?label=Sponsor&logo=github&color=EA4AAA)](https://github.com/sponsors/Huerte)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey)](https://github.com/Huerte/GitGo)

**Stop typing the same five Git commands. Run one instead.**

<a href="https://github.com/Huerte/GitGo/issues">Report Bug</a> · <a href="https://github.com/Huerte/GitGo/issues">Request Feature</a>

<br />

If GitGo saves you time, give it a star. If you want to go further, sponsoring helps keep it going.

<a href="https://github.com/sponsors/Huerte">
  <img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%9D%A4-EA4AAA?style=for-the-badge&logo=github" alt="Sponsor on GitHub" />
</a>

</div>

---

GitGo wraps your most-typed git commands into shorter ones. It covers init, scaffold, add, commit, push, branch, and stash. It also includes features most wrappers leave out: SSH key setup, HTTPS-to-SSH conversion, a named stash interface called state management, and a one-shot quickstart command that takes you from nothing to a live GitHub repo in seconds.

```bash
# Instead of this:
mkdir my-app && cd my-app && git init && git add . && git commit -m "init" && git remote add origin <url> && git push -u origin main

# Run this:
gitgo new my-app python
```

---

## Table of Contents

- [Demo](#demo)
- [Features](#features)
- [Installation Guide](#installation-guide)
- [Usage](#usage)
- [Command Reference](#command-reference)
- [How It Works](#how-it-works)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)
- [Changelog](CHANGELOG.md)
- [Contributing Guide](CONTRIBUTING.md)
- [First Contribution Walkthrough](docs/first-contribution.md)
- [Troubleshooting](docs/troubleshooting.md)

---

## Demo

![GitGo demo](assets/demo.gif)

---

## Features

- **Single commands for linking, pushing, and stashing.** No more chaining five commands together.
- **Quickstart with `new`:** One command to scaffold your project, create the GitHub repo, and push it. No switching tabs, no manual steps.
- **Project scaffolding with `init`:** Generates a language-specific project structure with a `.gitignore` from GitHub's official templates. Supports Python, Node, Rust, Go, C#, and more.
- **Remote repo creation with `repo`:** Creates a GitHub repo directly from the terminal without touching a browser.
- **Undo:** Roll back commits, unstage files, discard local changes, or revert pushes. The subcommands say what they do: `undo commit`, `undo add`, `undo changes`, `undo link`, `undo push`, `undo pull`.
- **Conflict resolution with `resolve`:** Finish a pull after fixing a merge conflict. Verifies the conflict markers are actually gone before staging and completing it. Back out anytime with `resolve --abort`.
- **Branch switching with `jump`:** Stashes your uncommitted work, moves to the target branch, syncs with main, and pops the stash. If a merge conflict occurs, the Try-and-Revert engine offers to roll the whole operation back.
- **State management:** Named, indexed stash. Run `state list` to see what you saved. No more `stash@{2}` archaeology.
- **Custom defaults:** Store your preferred branch name and default commit message. GitGo picks them up on every run.
- **Auto-update checker:** Checks PyPI for newer versions in a background thread. Results are cached for 7 days so startup isn't delayed.
- **SSH auto-setup & signing:** Generates an `ed25519` key, loads it into `ssh-agent`, opens your GitHub SSH settings page, and automatically signs all future commits for the verified badge.
- **HTTPS-to-SSH conversion:** Detects HTTPS remotes and rewrites them before pushing if SSH is configured. No manual `git remote set-url`.
- **Termux support:** Detects the Termux environment, adjusts install paths, uses `termux-open` for browser actions, and patches the dubious ownership Git error.
- **Safe interruptions:** Hitting `Ctrl+C` midway through a command automatically aborts in-progress merges, cleans up partial states, and tells you exactly what was and wasn't saved.

---

## Installation Guide

### Prerequisites

- **Python 3.8+**
- **Git 2.x+**: [git-scm.com](https://git-scm.com)
- **OpenSSH**: required for `gitgo user login` (pre-installed on most systems)
- A **GitHub account**

### Install from PyPI

For Windows users or environments without global pip restrictions:

```bash
pip install pygitgo
```

*(Alternatively, use `pipx install pygitgo` for an isolated environment.)*

### Install via pipx (Cross-Platform)

```bash
pipx install pygitgo
```

### Quick Install (Linux & macOS)

The install script creates an isolated environment and places `gitgo` in `~/.local/bin`. Useful for PEP 668-enforced systems:

```bash
curl -sSL https://raw.githubusercontent.com/Huerte/GitGo/main/install.sh | bash
```

Verify the installation:

```bash
gitgo -r
```

> **Note for Termux (Android):** GitGo detects the Termux environment automatically and adjusts install paths and browser behavior accordingly.

### Install from Source

```bash
git clone https://github.com/Huerte/GitGo.git
cd GitGo
pip install -e .
```

---

## Usage

### 1. Set Up Your Identity

Run this once on each machine you use. GitGo generates an SSH key, prints it for you to copy, and opens GitHub so you can add it. You add the same key twice: once as an **Authentication Key** (to push and pull), once as a **Signing Key** (so your commits show Verified). After that, GitGo tests the connection and sets up your Git identity automatically.

```bash
gitgo user login
```

For a full walkthrough with screenshots, see the [Login Guide](docs/login-guide.md).

### 2. Start a New Project From Scratch

One command scaffolds the local project, creates the GitHub repo, and pushes it. No tab switching.

```bash
gitgo new my-app python
gitgo new my-app rust --private
gitgo new my-app         # no scaffold, just the repo and push
```

Or use the individual steps if you want more control:

```bash
# Step 1: scaffold the project locally
gitgo init my-app python

# Step 2: create the remote GitHub repo
cd my-app
gitgo repo my-app --private

# Step 3: connect and push
gitgo link https://github.com/username/my-app.git
```

### 3. Link an Existing Project to GitHub

Point GitGo at an existing empty GitHub repo. It initializes Git, stages everything, commits, and pushes, including pulling unrelated histories if the remote isn't empty.

```bash
gitgo link https://github.com/username/repo.git "Initial commit"
```

### 4. Push Changes

```bash
# Push to an existing branch
gitgo push main "Fix auth bug"

# Create a new branch and push
gitgo push -n feat/login "Add login flow"
```

### 5. Switch Branches

Switch branches with uncommitted work in progress. `jump` stashes your changes, moves to the target branch, syncs with main, and pops the stash. If the pop triggers a conflict, it offers to abort and restore the repo to its prior state.

```bash
gitgo jump feat/new-login
```

### 6. Undo Mistakes

Undo recent mistakes with commands named for what they undo.

```bash
gitgo undo commit    # Undo the last commit (files stay staged)
gitgo undo add       # Unstage files
gitgo undo changes   # DANGER: permanently discard all uncommitted edits
gitgo undo link      # Remove remote and undo initial commit
gitgo undo push      # DANGER: Revert last push with a force-push
gitgo undo pull      # Revert the branch to its state before the last pull
```

### 7. Resolve a Merge Conflict

If `gitgo pull` hits a merge conflict, fix the conflict markers in your editor, then run:

```bash
gitgo resolve
```

GitGo checks that the conflicts are actually resolved, then stages the files and finishes the pull. Changed your mind mid-conflict?

```bash
gitgo resolve --abort
```

### 8. Save Your Work-in-Progress

```bash
gitgo state save "halfway through refactor"
gitgo state list
gitgo state load 1
```

### 9. Custom Defaults

```bash
gitgo config set default-branch develop
gitgo config set default-message "WIP: updates"
gitgo config get default-branch
```

---

## Command Reference

### `gitgo new`

One-shot quickstart. Scaffolds a local project, creates the GitHub remote repo, and pushes, all in one command.

```bash
gitgo new <name> [lang]
gitgo new my-app python            # scaffold Python project and push
gitgo new my-app rust --private    # private Rust project
gitgo new my-app                   # no scaffold, just create repo and push
```

| Flag | Description |
|------|-------------|
| `lang` | Language to scaffold. Options: `python`, `node`, `rust`, `go`, `cs`, and more |
| `--template OWNER/REPO` | Use a GitHub template repo instead of a language scaffold |
| `-p`, `--private` | Create a private repository |
| `-d`, `--description TEXT` | Short description shown on GitHub |

### `gitgo init`

Scaffolds a project folder locally. Creates a README, `.gitignore` (fetched from GitHub's official templates), and language-specific starter files.

```bash
gitgo init my-app python                                       # generates pyproject.toml and .python-version
gitgo init my-app node                                         # generates package.json and index.js
gitgo init my-app cs                                           # generates .csproj and Program.cs
gitgo init my-app --template owner/repo                        # slug format
gitgo init my-app --template https://github.com/owner/repo    # full URL accepted too
```

Supported languages: `python` (`py`), `node` (`js`, `ts`), `rust` (`rs`), `go` (`golang`), `csharp` (`cs`), and any language with a `.gitignore` template on GitHub.

### `gitgo repo`

Creates a remote GitHub repository without touching your local files.

```bash
gitgo repo [name]                  # use current directory name if no name given
gitgo repo my-app --private
gitgo repo my-app -d "My project description"
```

| Flag | Description |
|------|-------------|
| `-p`, `--private` | Create a private repository |
| `-d`, `--description TEXT` | Short description shown on GitHub |

On first run, GitGo opens GitHub's PAT page and prompts you to paste a token with `repo` scope. The token is saved to git config for future calls. If the token expires, GitGo detects the 401 and re-prompts automatically.

### `gitgo push`

Stage, commit, and push in one command.

```bash
gitgo push [branch] [message]
gitgo push -n [branch] [message]   # create new branch first
gitgo push -s [branch] [message]   # interactively select files to stage
```

> [!TIP]
> Use `gitgo push -h` to see all available flags and examples.

| Flag | Description |
|------|-------------|
| `-n`, `--new` | Create a new branch before pushing |
| `-s`, `--select` | Interactively select which files to include in the push |

If there are no new changes but unpushed commits exist, GitGo detects this and pushes without creating an empty commit.

### `gitgo pull`

Pulls updates from the remote. Stashes any uncommitted work first, runs a rebase pull, then pops the stash.

```bash
gitgo pull             # Pull updates for the current branch
gitgo pull <branch>    # Pull updates from a specific branch
```

### `gitgo link`

Initializes a Git repository, connects it to a remote, and pushes. Works on already-initialized repos and handles unrelated histories.

```bash
gitgo link <github_repo_url> [commit_message]
```

### `gitgo jump`

Switches branches with uncommitted work in progress. Stashes changes, moves to the target branch, pulls from main, and pops the stash. If the pop triggers a merge conflict, the Try-and-Revert engine offers to abort the entire operation and restore the repo to the state it was in before the command ran.

```bash
gitgo jump <branch>
```

### `gitgo undo`

Undo recent actions with subcommands named for what they undo.

```bash
gitgo undo commit    # Undo the last commit without losing files
gitgo undo add       # Unstage files
gitgo undo changes   # Permanently discard all new files and uncommitted edits
gitgo undo link      # Remove the remote and undo the initial commit
gitgo undo push      # DANGER: Revert the last push with a force-push
gitgo undo pull      # Revert the branch to its state before the last pull
```

### `gitgo state`

Named, indexed interface over `git stash`.

```bash
gitgo state list              # show all saved states
gitgo state save [name]       # save current work (default name: Auto-Save)
gitgo state load [id]         # restore a state by index
gitgo state delete [id]       # delete a state by index
gitgo state delete -a         # delete all saved states
```

*Short aliases:* `-l`, `-s`, `-o`, `-d`

### `gitgo user`

```bash
gitgo user              # show current Git identity
gitgo user login        # generate SSH key and configure Git identity
gitgo user logout       # remove SSH keys and Git identity config
```

### `gitgo config`

Manage your GitGo defaults.

```bash
gitgo config set <key> <value>
gitgo config get <key>
```

| Key | Description | Default |
|-----|-------------|---------|
| `default-branch` | The branch used for push/link | `main` |
| `default-message` | The commit message used for push | `chore: new changes applied` |

### Global Flags

```bash
gitgo help      # show complete manual
gitgo <cmd> -h  # show help for a specific command
gitgo -v        # version
gitgo -r        # verify GitGo is ready
```

---

## How It Works

- **SSH Auto-Setup & Signing:** `gitgo user login` generates an `ed25519` SSH key and prompts you to add it to GitHub twice (for authentication and signing). GitGo then injects temporary `-c` flags into every commit to automatically sign them with this key, without touching your global git config.
- **HTTPS to SSH Conversion:** If your remote is set to HTTPS and SSH is configured, GitGo rewrites the remote before pushing. No `git remote set-url` required.
- **Auto-Update Checker:** Spawns a non-blocking background thread on startup to query PyPI for newer versions. Results are cached locally for 7 days to prevent unnecessary network requests.
- **Termux Compatibility:** Detects Termux via environment variables, adjusts binary locations (`$PREFIX/bin`), uses `termux-open` for browser actions, and patches the `detected dubious ownership` Git error.
- **State Management:** `gitgo state` wraps `git stash` with named saves, indexed listing, and confirmation prompts.

---

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including project structure, test instructions, commit conventions, and a [Good First Issues](CONTRIBUTING.md#good-first-issues) table if you're not sure where to start.

If this is your first time contributing to an open-source project, follow our step-by-step [First Contribution Walkthrough](docs/first-contribution.md) guide.

---

## Credits

<div align="center">
  <table>
    <tr>
      <td align="center"><a href="https://github.com/Huerte"><img src="https://github.com/Huerte.png" width="80px;" alt=""/></a><br /><a href="https://github.com/Huerte"><b>Huerte</b></a><br />Creator</td>
      <td align="center"><a href="https://github.com/Venomous-pie"><img src="https://github.com/Venomous-pie.png" width="80px;" alt=""/></a><br /><a href="https://github.com/Venomous-pie"><b>Venomous-pie</b></a><br />Contributor</td>
    </tr>
  </table>
</div>

---

## License

Distributed under the **GPLv3** License. See [`LICENSE`](LICENSE) for details.

---

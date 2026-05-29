<div align="center">

![GitGo Banner](assets/banner.png)

[![Tests](https://github.com/Huerte/GitGo/actions/workflows/tests.yml/badge.svg)](https://github.com/Huerte/GitGo/actions)
[![PyPI version](https://img.shields.io/pypi/v/pygitgo?color=blue&label=PyPI)](https://pypi.org/project/pygitgo)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pygitgo?color=blue)](https://pypi.org/project/pygitgo)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Ko-fi](https://img.shields.io/badge/Support-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/huerte)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey)](https://github.com/Huerte/GitGo)

**Stop typing the same five Git commands. Run one instead.**

<a href="https://github.com/Huerte/GitGo/issues">Report Bug</a> · <a href="https://github.com/Huerte/GitGo/issues">Request Feature</a>

<br />

If GitGo saves you time, consider buying me a coffee. It helps keep the project going.

<a href="https://ko-fi.com/huerte">
  <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support on Ko-fi" />
</a>

</div>

---

GitGo wraps your most-typed git commands into shorter ones. It covers init, add, commit, push, branch, and stash. It also includes features most wrappers leave out: SSH key setup, HTTPS-to-SSH conversion, and a named stash interface called state management.

```bash
# Instead of this:
git init && git add . && git commit -m "init" && git remote add origin <url> && git push -u origin main

# Run this:
gitgo link https://github.com/username/repo.git "init"
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

---

## Demo

![GitGo demo](assets/demo.gif)

---

## Features

- **Single commands for linking, pushing, and stashing.** No more chaining five commands together.
- **Undo:** Roll back commits, unstage files, or discard local changes. The subcommands say what they do: `undo commit`, `undo add`, `undo changes`.
- **Branch switching with `jump`:** Stashes your uncommitted work, moves to the target branch, syncs with main, and pops the stash. If a merge conflict occurs, the Try-and-Revert engine offers to roll the whole operation back.
- **State management:** Named, indexed stash. Run `state list` to see what you saved. No more `stash@{2}` archaeology.
- **Custom defaults:** Store your preferred branch name and default commit message. GitGo picks them up on every run.
- **Auto-update checker:** Checks PyPI for newer versions in a background thread. Results are cached for 7 days so startup isn't delayed.
- **SSH auto-setup:** Generates an `ed25519` key, loads it into `ssh-agent`, and opens your GitHub SSH settings page.
- **HTTPS-to-SSH conversion:** Detects HTTPS remotes and rewrites them before pushing if SSH is configured. No manual `git remote set-url`.
- **Termux support:** Detects the Termux environment, adjusts install paths, uses `termux-open` for browser actions, and patches the dubious ownership Git error.

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

Run this once on a new machine. GitGo generates an SSH key, adds it to `ssh-agent`, prints the public key, and opens your GitHub SSH settings page.

```bash
gitgo user login
```

### 2. Link a New Project to GitHub

Point GitGo at an existing empty GitHub repo. It initializes Git, stages everything, commits, and pushes — including pulling unrelated histories if the remote isn't empty.

```bash
gitgo link https://github.com/username/repo.git "Initial commit"
```

### 3. Push Changes

```bash
# Push to an existing branch
gitgo push main "Fix auth bug"

# Create a new branch and push
gitgo push -n feat/login "Add login flow"
```

### 4. Switch Branches

Switch branches with uncommitted work in progress. `jump` stashes your changes, moves to the target branch, syncs with main, and pops the stash. If the pop triggers a conflict, it offers to abort and restore the repo to its prior state.

```bash
gitgo jump feat/new-login
```

### 5. Undo Mistakes

Undo recent mistakes with commands named for what they undo.

```bash
gitgo undo commit    # Undo the last commit (files stay staged)
gitgo undo add       # Unstage files
gitgo undo changes   # DANGER: permanently discard all uncommitted edits
```

### 6. Save Your Work-in-Progress

```bash
gitgo state save "halfway through refactor"
gitgo state list
gitgo state load 1
```

### 7. Custom Defaults

```bash
gitgo config set default-branch develop
gitgo config set default-message "WIP: updates"
gitgo config get default-branch
```

---

## Command Reference

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
| `default-message` | The commit message used for push | `New Project Update` |

### Global Flags

```bash
gitgo help      # show complete manual
gitgo <cmd> -h  # show help for a specific command
gitgo -v        # version
gitgo -r        # verify GitGo is ready
```

---

## How It Works

- **SSH Auto-Setup:** `gitgo user login` generates an `ed25519` SSH key, adds it to `ssh-agent`, prints the public key, and opens `github.com/settings/ssh/new`.
- **HTTPS to SSH Conversion:** If your remote is set to HTTPS and SSH is configured, GitGo rewrites the remote before pushing. No `git remote set-url` required.
- **Auto-Update Checker:** Spawns a non-blocking background thread on startup to query PyPI for newer versions. Results are cached locally for 7 days to prevent unnecessary network requests.
- **Termux Compatibility:** Detects Termux via environment variables, adjusts binary locations (`$PREFIX/bin`), uses `termux-open` for browser actions, and patches the `detected dubious ownership` Git error.
- **State Management:** `gitgo state` wraps `git stash` with named saves, indexed listing, and confirmation prompts.

---

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including project structure, test instructions, commit conventions, and a [Good First Issues](CONTRIBUTING.md#good-first-issues) table if you're not sure where to start.

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
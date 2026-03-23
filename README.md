<div align="center">

# GitGo

[![Tests](https://github.com/Huerte/GitGo/actions/workflows/tests.yml/badge.svg)](https://github.com/Huerte/GitGo/actions)
[![PyPI version](https://img.shields.io/pypi/v/pygitgo?color=blue&label=PyPI)](https://pypi.org/project/pygitgo)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pygitgo?color=blue)](https://pypi.org/project/pygitgo)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey)](https://github.com/Huerte/GitGo)

**Stop typing the same five Git commands. Run one instead.**

<a href="https://github.com/Huerte/GitGo/issues">Report Bug</a> · <a href="https://github.com/Huerte/GitGo/issues">Request Feature</a>

</div>

---

GitGo wraps your most repetitive Git operations — init, add, commit, push, branch, stash — into short, memorable commands. It also handles the friction points most tools ignore: automatic SSH setup, HTTPS-to-SSH conversion, and a human-friendly stash interface called **state management**.

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
- [License](#license)

---

## Demo

![GitGo demo](assets/demo.gif)

---

## Features

GitGo provides a CLI environment designed for faster and simpler Git workflows. Built to be intuitive, fast, and frictionless.

- **Simplified Git Operations:** Replaces chained commands with single intuitive commands for linking, pushing, and stashing.
- **Smart Branch Hopping:** Safely traverse branches with `jump`. Auto-stashes messy code and prevents merge conflict disasters with a Try-And-Revert safety engine.
- **State Management:** A human-readable interface over `git stash`. States are named and listed by index so you never have to remember cryptic stash references.
- **SSH Auto-Setup:** Generates an SSH key, adds it to `ssh-agent`, and opens your GitHub settings automatically.
- **HTTPS to SSH Conversion:** Silently converts the remote to SSH before pushing if your SSH is configured.
- **Termux Compatibility:** Works natively on Android natively handling common issues like dubious ownership errors.

---

## Installation Guide

### Prerequisites

- **Python 3.8+**
- **Git 2.x+** — [git-scm.com](https://git-scm.com)
- **OpenSSH** — required for `gitgo user login` (pre-installed on most systems)
- A **GitHub account**

### Install from PyPI

```bash
pip install pygitgo
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
On first use, run the login wizard. GitGo generates an SSH key, prints the public key, and opens your GitHub SSH settings page automatically.
```bash
gitgo user login
```

### 2. Link a New Project to GitHub
Point GitGo at an existing empty GitHub repository. It will initialize Git, stage everything, make the first commit, and push — handling branch naming and merge conflicts automatically.
```bash
gitgo link https://github.com/username/repo.git "Initial commit"
```

### 3. Push Changes
```bash
# Push to an existing branch
gitgo push main "Fix auth bug"

# Create a new branch and push
gitgo push -n feature/login "Add login flow"
```

### 4. Safely Switch Branches
Jump to a different branch without worrying about your uncommitted changes. GitGo will safely stash them, hop to the new branch, sync with `main`, and carefully unpack them.
```bash
gitgo jump feature/new-login
```

### 5. Save Your Work-in-Progress
```bash
gitgo state save "halfway through refactor"
gitgo state list
gitgo state load 1
```

---

## Command Reference

### `gitgo push`

Stages all changes, commits, and pushes in one command.

```bash
gitgo push [branch] [message]
gitgo push -n [branch] [message]   # create new branch first
```

| Flag | Description |
|------|-------------|
| `-n`, `--new` | Create a new branch before pushing |

If there are no new changes but unpushed commits exist, GitGo detects this and pushes without creating an empty commit.

### `gitgo link`

Initializes a Git repository in the current directory, connects it to a remote, and pushes. Handles already-initialized repos gracefully and pulls unrelated histories.

```bash
gitgo link <github_repo_url> [commit_message]
```

### `gitgo jump`

Safely switches branches without losing uncommitted progress. Auto-stashes, jumps, pulls from `main`, and unpacks. If applying the stash triggers a merge conflict, the built-in Try-and-Revert engine will offer to safely cancel the entire operation and instantly rewind your repository to exactly how it was before the command.

```bash
gitgo jump <branch>
```

### `gitgo state`

A human-readable interface over `git stash`.

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

### Global Flags

```bash
gitgo -h        # help
gitgo -v        # version
gitgo -r        # verify GitGo is ready
```

---

## How It Works

- **SSH Auto-Setup:** `gitgo user login` generates an `ed25519` SSH key, adds it to `ssh-agent`, prints the public key, and opens `github.com/settings/ssh/new`.
- **HTTPS to SSH Conversion:** If your remote is set to HTTPS, GitGo converts the remote to SSH before pushing if SSH is configured. No `git remote set-url` is required.
- **Termux Compatibility:** Detects Termux via environment variables, adjusts binary locations (`$PREFIX/bin`), uses `termux-open` for browser actions, and natively handles the `detected dubious ownership` Git error.
- **State Management:** `gitgo state` wraps `git stash` with named saves, indexed listing, and confirmation prompts.

---

## Contributing

Contributions are welcome and appreciated!

1. Fork the Project
2. Create a Feature Branch (`git checkout -b feature/your-feature`)
3. Commit Changes
4. Push to the Branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## Credits

<div align="center">
  <table>
    <tr>
      <td align="center"><a href="https://github.com/Huerte"><img src="https://github.com/Huerte.png" width="80px;" alt=""/></a><br /><a href="https://github.com/Huerte"><b>Huerte</b></a><br />Creator</td>
      <td align="center"><a href="https://github.com/Venomous-pie"><img src="https://github.com/Venomous-pie.png" width="80px;" alt=""/></a><br /><a href="https://github.com/Venomous-pie"><b>Venomous-pie</b></a><br />Core Contributor</td>
    </tr>
  </table>
</div>

---

## License

Distributed under the **GPLv3** License. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
<sub>Created by <a href="https://github.com/Huerte">Huerte</a> with core contributions from <a href="https://github.com/Venomous-pie">Venomous-pie</a></sub>
</div>

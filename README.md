<div align="center">

<h1>GitGo</h1>

<p><strong>Stop typing the same five Git commands. Run one instead.</strong></p>

[![PyPI version](https://img.shields.io/pypi/v/pygitgo?color=blue&label=PyPI)](https://pypi.org/project/pygitgo)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey)](https://github.com/Huerte/GitGo)

<!-- Replace this comment with a demo GIF: record with asciinema or terminalizer -->
<!-- ![GitGo demo](https://raw.githubusercontent.com/Huerte/GitGo/main/assets/demo.gif) -->

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

## Contents

- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [How It Works](#how-it-works)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

```bash
pip install pygitgo
```

Verify the install:

```bash
gitgo -r
```

> **Termux (Android):** Works natively. GitGo detects the Termux environment automatically and adjusts install paths and browser behavior accordingly.

### Install from source

```bash
git clone https://github.com/Huerte/GitGo.git
cd GitGo
pip install -e .
```

---

## Prerequisites

- **Python 3.8+**
- **Git 2.x+** — [git-scm.com](https://git-scm.com)
- **OpenSSH** — required for `gitgo user login` (pre-installed on most systems)
- A **GitHub account**

---

## Quick Start

### 1. Set up your identity

On first use, run the login wizard. GitGo generates an SSH key, prints the public key, and opens your GitHub SSH settings page automatically.

```bash
gitgo user login
```

### 2. Link a new project to GitHub

Point GitGo at an existing empty GitHub repository. It will initialize Git, stage everything, make the first commit, and push — handling branch naming and merge conflicts with an existing remote automatically.

```bash
gitgo link https://github.com/username/repo.git "Initial commit"
```

### 3. Push changes

```bash
# Push to an existing branch
gitgo push main "Fix auth bug"

# Create a new branch and push
gitgo push -n feature/login "Add login flow"
```

### 4. Save your work-in-progress

```bash
gitgo state save "halfway through refactor"
gitgo state list
gitgo state load 1
```

---

## Command Reference

### `gitgo push`

Stages all changes, commits, and pushes in one command.

```
gitgo push [branch] [message]
gitgo push -n [branch] [message]   # create new branch first
```

| Flag | Description |
|------|-------------|
| `-n`, `new` | Create a new branch before pushing |

If there are no new changes but unpushed commits exist, GitGo detects this and pushes without creating an empty commit.

---

### `gitgo link`

Initializes a Git repository in the current directory, connects it to a remote, and pushes. Handles an already-initialized repo gracefully, and pulls unrelated histories automatically if the remote already has commits.

```
gitgo link <github_repo_url> [commit_message]
```

---

### `gitgo state`

A human-readable interface over `git stash`. States are named and listed by index so you never have to remember `stash@{2}`.

```
gitgo state list              # show all saved states
gitgo state save [name]       # save current work (default name: Auto-Save)
gitgo state load [id]         # restore a state by index
gitgo state delete [id]       # delete a state by index
gitgo state delete -a         # delete all saved states
```

Short aliases: `-l`, `-s`, `-o`, `-d`

---

### `gitgo user`

```
gitgo user              # show current Git identity
gitgo user login        # generate SSH key and configure Git identity
gitgo user logout       # remove SSH keys and Git identity config
```

---

### Global flags

```
gitgo -h        # help
gitgo -v        # version
gitgo -r        # verify GitGo is ready
```

---

## How It Works

**SSH auto-setup** — `gitgo user login` generates an `ed25519` SSH key, adds it to `ssh-agent`, prints the public key, and opens `github.com/settings/ssh/new` in your browser. After you add the key, GitGo verifies the connection automatically.

**HTTPS to SSH conversion** — If your remote is set to an HTTPS URL and your SSH is configured, GitGo silently converts the remote to SSH before pushing. No manual `git remote set-url` required.

**Termux compatibility** — GitGo detects Termux via environment variables and file paths, adjusts binary locations (`$PREFIX/bin`), uses `termux-open` for browser actions, and handles the `detected dubious ownership` Git error that commonly appears in shared Android storage.

**State management** — `gitgo state` wraps `git stash` with named saves, indexed listing, and confirmation prompts. Under the hood it uses `git stash push -m`, `git stash apply`, and `git stash drop`.

---

## Contributing

Issues and pull requests are welcome.

1. Fork the repository
2. Create a branch: `git checkout -b fix/your-fix`
3. Make your change and add tests if applicable
4. Push and open a PR against `main`

Please open an issue first for significant changes so we can discuss the approach.

---

## License

GPLv3 — see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>Built by <a href="https://github.com/Huerte">Jerald Huerte</a> · Cantilan, Surigao del Sur, Philippines</sub>
</div>

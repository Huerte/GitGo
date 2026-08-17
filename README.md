<div align="center">

![GitGo Banner](assets/banner.png)

### Stop typing the same five Git commands. Run one instead.

[![Tests](https://github.com/Huerte/GitGo/actions/workflows/tests.yml/badge.svg)](https://github.com/Huerte/GitGo/actions)
[![Codecov](https://codecov.io/gh/Huerte/GitGo/branch/main/graph/badge.svg)](https://codecov.io/gh/Huerte/GitGo)
[![PyPI version](https://img.shields.io/pypi/v/pygitgo?color=blue&label=PyPI)](https://pypi.org/project/pygitgo)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pygitgo?color=blue)](https://pypi.org/project/pygitgo)
[![Winget](https://img.shields.io/badge/winget-Huerte.GitGo-blue?logo=windows&logoColor=white)](https://github.com/microsoft/winget-pkgs/tree/master/manifests/h/Huerte/GitGo)  
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/Huerte?label=Sponsor&logo=github&color=EA4AAA)](https://github.com/sponsors/Huerte)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Termux-lightgrey)](https://github.com/Huerte/GitGo)

**We won't let you nuke your work by accident.** GitGo features DANGER-red prompts before destructive operations, a Try-and-Revert engine that cleanly rolls back merge conflicts, and safe `Ctrl+C` aborts to keep your code safe.

[Report Bug](https://github.com/Huerte/GitGo/issues) · [Request Feature](https://github.com/Huerte/GitGo/issues)

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

- **One command instead of five.** `push`, `link`, `sync`, and `jump` combine the git commands you'd normally type out by hand.
- **Won't let you nuke your work by accident.** Destructive commands like `undo changes` and `undo push` ask for confirmation first, and hitting Ctrl+C mid-command always leaves your repo in a clean, known state.
- **Fixes merge conflicts without leaving you stuck in an editor.** `resolve` checks that the conflict markers are actually gone before finishing the pull. If you get stuck, `resolve --abort` or `undo pull` puts things back the way they were.
- **Works with any Git host.** GitHub, GitLab, Gitea, self-hosted, all of it. A GitHub account is only needed for `repo` and `new`, since those two create the remote repo through GitHub's API.
- **`new` takes you from nothing to a live repo in one command.** Scaffolds the project, creates the GitHub repo, and pushes it. No switching tabs.
- **`init` scaffolds a project locally.** Generates a README, a `.gitignore` pulled from GitHub's official templates, and starter files for Python, Node, Rust, Go, C#, and more.
- **`repo` creates a GitHub repo from your terminal.** No browser needed.
- **`jump` switches branches without losing your work.** Stashes what you're doing, moves to the target branch, pulls the latest, then restores your work. If that causes a conflict, GitGo offers to undo the whole thing and put you back where you started.
- **`state` replaces `git stash` with something you can actually read.** Named, numbered snapshots. Run `state list` to see what you saved instead of guessing what `stash@{2}` was.
- **`log` shows your commit history in a readable, color-coded view.**
- **Set your own defaults.** Store your usual branch name and commit message once with `config`, and GitGo uses them every time after.
- **SSH setup and commit signing, handled for you.** `user login` generates a key, loads it into `ssh-agent`, and signs your future commits so they show up as Verified on GitHub.
- **Works out of the box in Termux.** GitGo detects Termux, adjusts install paths, and fixes the common "dubious ownership" Git error automatically.
- **Checks for updates in the background.** No delay on startup; results are cached for a week.

---

## Installation Guide

### Prerequisites

- **Python 3.8+**: not required if installing via winget or the standalone executable
- **Git 2.x+**: [git-scm.com](https://git-scm.com)
- **OpenSSH**: required for `gitgo user login` (pre-installed on most systems)
- A **GitHub account**: only required for `gitgo repo` and `gitgo new`, which create the remote repo for you through GitHub's API. Every other command works with any Git remote, GitHub or not.

### Quick Install (Recommended)

The install scripts create an isolated Python virtual environment in `~/.gitgo/venv` and add the `gitgo` executable to your PATH. This safely avoids conflicts with system Python packages (PEP 668).

#### Windows

**Via winget** (Windows 10 1709+ / Windows 11):

```powershell
winget install gitgo
```

This installs a standalone executable. No Python needed, and updates are one line:

```powershell
winget upgrade gitgo
```

**Via install script** (requires Python 3.8+):

```powershell
irm https://raw.githubusercontent.com/Huerte/GitGo/main/install.ps1 | iex
```

#### Linux & macOS

```bash
curl -sSL https://raw.githubusercontent.com/Huerte/GitGo/main/install.sh | bash
```

Verify the installation:

```bash
gitgo -r
```

> **Note for Termux (Android):** GitGo detects the Termux environment automatically and adjusts install paths and browser behavior accordingly. Run the Linux installation command above.

### Alternative Installation Methods

#### Install via pipx (Cross-Platform)

If you prefer managing Python CLI tools with `pipx`:

```bash
pipx install pygitgo
```

#### Install from PyPI

For environments without global pip restrictions:

```bash
pip install pygitgo
```

#### Install from Source

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

**How arguments work:**
- Two arguments: first is the branch, second is the commit message.
- One argument: if it matches an existing branch, it is used as the branch; otherwise it is used as the commit message and the current branch is used.
- No arguments: GitGo always pushes to whatever branch you're currently on, it doesn't read `default-branch` for this. Only the commit message falls back to your configured default. Both are shown before anything happens, for example:
  ```
  No branch given. Using current branch: 'feature/login'
  No commit message given. Using: 'chore: new changes applied'
  ```
  You can change the default commit message with `gitgo config set default-message`.

If there are no new changes but unpushed commits exist, GitGo detects this and pushes without creating an empty commit.

### `gitgo pull`

Pulls updates from the remote. Stashes any uncommitted work first, runs a rebase pull, then pops the stash.

```bash
gitgo pull             # Pull updates for the current branch
gitgo pull <branch>    # Pull updates from a specific branch
```

### `gitgo sync`

Pulls the latest changes with `--rebase` and `--autostash`, commits your work, then pushes everything in one step.

```bash
gitgo sync [message]
```

### `gitgo link`

Connects a local project to a remote repository. Initializes Git if needed, stages everything, commits, and pushes. Works on already-initialized repos too, and handles unrelated histories.

```bash
gitgo link <repo_url> [commit_message]
```

### `gitgo jump`

Switches to another branch while saving your current work automatically. Stashes your changes, moves to the target branch, pulls from main, then restores your work. If restoring causes a conflict, the Try-and-Revert engine offers to cancel the whole operation and put everything back.

```bash
gitgo jump <branch>
```

### `gitgo undo`

Undo recent actions with subcommands named for what they undo.

```bash
gitgo undo commit    # Undo the last commit without losing files
gitgo undo add       # Unstage files
gitgo undo changes   # DANGER (destructive): permanently discard all uncommitted edits
gitgo undo link      # Remove the remote and undo the initial commit
gitgo undo push      # DANGER (destructive): revert the last push with a force-push
gitgo undo pull      # Revert the branch to its state before the last pull
```

### `gitgo state`

Save and restore snapshots of your work-in-progress. Built on top of `git stash` with named saves and numbered access.

```bash
gitgo state list              # show all saved snapshots
gitgo state save [name]       # save current work (default name: Auto-Save)
gitgo state load [id]         # restore a snapshot by its number
gitgo state delete [id]       # delete a snapshot by its number
gitgo state delete -a         # delete all saved snapshots
```

### `gitgo log`

Show commit history with a color-coded output.

```bash
gitgo log                  # show last 5 commits for current branch
gitgo log -n 10            # show last 10 commits
gitgo log -b main          # show commits for the main branch
```

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
gitgo --help      # show complete manual
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

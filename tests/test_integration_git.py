import os
import subprocess
from pathlib import Path


def _git(cwd, *args):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def test_integration_init_commit_and_branch(tmp_path):
    repo = tmp_path / "project"
    repo.mkdir()

    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-m", "Initial commit")

    log = _git(repo, "log", "-1", "--pretty=%s")
    assert log.stdout.strip() == "Initial commit"

    branch = _git(repo, "branch", "--show-current")
    assert branch.stdout.strip() == "main"


def test_integration_bare_remote_and_push(tmp_path):
    bare = tmp_path / "remote.git"
    work = tmp_path / "project"
    work.mkdir()

    _git(tmp_path, "init", "--bare", str(bare))
    _git(work, "init", "-b", "main")
    _git(work, "remote", "add", "origin", str(bare))
    (work / "file.txt").write_text("content\n", encoding="utf-8")
    _git(work, "add", "file.txt")
    _git(work, "-c", "commit.gpgsign=false", "commit", "-m", "first")
    _git(work, "push", "-u", "origin", "main")

    ls = _git(bare, "branch")
    assert "main" in ls.stdout


def test_integration_stash_save_and_list(tmp_path):
    repo = tmp_path / "project"
    repo.mkdir()

    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-m", "initial")

    (repo / "wip.txt").write_text("draft\n", encoding="utf-8")
    _git(repo, "add", "wip.txt")
    _git(repo, "stash", "push", "-m", "GitGo Auto-Save")

    stash_list = _git(repo, "stash", "list")
    assert "GitGo Auto-Save" in stash_list.stdout

    status = _git(repo, "status", "--porcelain")
    assert status.stdout.strip() == ""

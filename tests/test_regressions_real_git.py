"""Regression tests that run REAL git in temp repos (no mocking of run_command).

Each test reproduces a bug found while auditing v1.10.4.
"""
from argparse import Namespace
from pathlib import Path
import io
import subprocess
import sys

import pytest

from pygitgo.exceptions import GitGoError


def git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / ".gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    git("config", "--global", "user.name", "Test User")
    git("config", "--global", "user.email", "test@example.com")
    git("config", "--global", "init.defaultBranch", "main")
    git("config", "--global", "commit.gpgsign", "false")
    return tmp_path


def make_remote_and_clones(root):
    remote = root / "remote.git"
    git("init", "-q", "--bare", "-b", "main", str(remote))
    one, two = root / "one", root / "two"
    git("clone", "-q", str(remote), str(one))
    (one / "f.txt").write_text("base\n")
    git("add", ".", cwd=one)
    git("commit", "-qm", "base", cwd=one)
    git("push", "-q", "origin", "main", cwd=one)
    git("clone", "-q", str(remote), str(two))
    return remote, one, two


# ---------- bug 4: file picker path parsing ----------

def test_changed_files_keep_full_paths_and_unquoted_names(env, monkeypatch):
    from pygitgo.commands.staging import get_changed_files, selective_stage

    repo = env / "repo"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    (repo / "app.py").write_text("a\n")
    (repo / "util.py").write_text("b\n")
    git("add", ".", cwd=repo)
    git("commit", "-qm", "init", cwd=repo)
    (repo / "app.py").write_text("changed\n")
    (repo / "util.py").write_text("changed\n")
    (repo / "my notes.txt").write_text("new\n")
    monkeypatch.chdir(repo)

    paths = [f["path"] for f in get_changed_files()]
    assert paths == ["app.py", "util.py", "my notes.txt"]

    selective_stage(paths)  # must not raise: git accepts every path
    assert set(git("diff", "--cached", "--name-only", cwd=repo).splitlines()) == {
        "app.py", "util.py", "my notes.txt"}


def test_changed_files_handles_renames(env, monkeypatch):
    from pygitgo.commands.staging import get_changed_files

    repo = env / "repo"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    (repo / "old.txt").write_text("x\n")
    git("add", ".", cwd=repo)
    git("commit", "-qm", "init", cwd=repo)
    git("mv", "old.txt", "new.txt", cwd=repo)
    monkeypatch.chdir(repo)

    files = get_changed_files()
    assert [f["path"] for f in files] == ["new.txt"]


# ---------- bug 3: resolve must not commit conflict markers ----------

def _make_conflict(env, monkeypatch):
    from pygitgo.commands.pull import pull_operation

    _, one, two = make_remote_and_clones(env)
    (two / "f.txt").write_text("from teammate\n")
    git("commit", "-qam", "teammate edit", cwd=two)
    git("push", "-q", "origin", "main", cwd=two)
    (one / "f.txt").write_text("from me\n")
    git("commit", "-qam", "my edit", cwd=one)
    monkeypatch.chdir(one)
    with pytest.raises(GitGoError):
        pull_operation(Namespace(branch=None))
    return one


def test_resolve_refuses_while_markers_remain(env, monkeypatch):
    from pygitgo.commands.resolve import resolve_operation

    one = _make_conflict(env, monkeypatch)
    assert "<<<<<<<" in (one / "f.txt").read_text()

    with pytest.raises(GitGoError, match="Nothing was staged"):
        resolve_operation(Namespace(abort=False))

    # rebase must still be paused and nothing staged
    assert (one / ".git" / "rebase-merge").exists() or (one / ".git" / "rebase-apply").exists()
    assert "f.txt" in git("diff", "--name-only", "--diff-filter=U", cwd=one)


def test_resolve_completes_after_real_fix_and_only_stages_conflicted_files(env, monkeypatch):
    from pygitgo.commands.resolve import resolve_operation

    one = _make_conflict(env, monkeypatch)
    (one / "f.txt").write_text("merged by hand\n")
    (one / "unrelated.txt").write_text("should stay untracked\n")

    resolve_operation(Namespace(abort=False))

    assert git("show", "HEAD:f.txt", cwd=one) == "merged by hand"
    assert "unrelated.txt" not in git("ls-tree", "-r", "--name-only", "HEAD", cwd=one)


# ---------- bug 2: undo pull ----------

def test_undo_pull_ignores_unrelated_orig_head_and_keeps_uncommitted_work(env, monkeypatch):
    from pygitgo.commands.git_core import abort_pull_conflict
    from pygitgo.commands.undo import undo_commit

    repo = env / "repo"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    (repo / "a.txt").write_text("1\n")
    git("add", ".", cwd=repo)
    git("commit", "-qm", "c1", cwd=repo)
    (repo / "a.txt").write_text("1\n2\n")
    git("commit", "-qam", "c2", cwd=repo)
    monkeypatch.chdir(repo)

    undo_commit()  # sets ORIG_HEAD, but nothing was ever pulled
    (repo / "precious.txt").write_text("keep me\n")
    git("add", "precious.txt", cwd=repo)

    monkeypatch.setattr("pygitgo.utils.cli_io.confirm", lambda *a, **k: True)
    assert abort_pull_conflict() is False

    assert (repo / "precious.txt").read_text() == "keep me\n"


def test_undo_pull_restores_pre_pull_head_and_keeps_local_edits(env, monkeypatch):
    from pygitgo.commands.git_core import abort_pull_conflict
    from pygitgo.commands.pull import pull_operation

    _, one, two = make_remote_and_clones(env)
    (two / "new.txt").write_text("remote change\n")
    git("add", ".", cwd=two)
    git("commit", "-qm", "remote commit", cwd=two)
    git("push", "-q", "origin", "main", cwd=two)

    monkeypatch.chdir(one)
    before = git("rev-parse", "HEAD", cwd=one)
    pull_operation(Namespace(branch=None))
    assert git("rev-parse", "HEAD", cwd=one) != before

    (one / "wip.txt").write_text("uncommitted\n")  # untracked work survives reset --keep
    monkeypatch.setattr("pygitgo.utils.cli_io.confirm", lambda *a, **k: True)
    assert abort_pull_conflict() is True

    assert git("rev-parse", "HEAD", cwd=one) == before
    assert (one / "wip.txt").read_text() == "uncommitted\n"


def test_undo_pull_refuses_when_branch_moved_since_pull(env, monkeypatch):
    from pygitgo.commands.git_core import abort_pull_conflict
    from pygitgo.commands.pull import pull_operation

    _, one, two = make_remote_and_clones(env)
    (two / "new.txt").write_text("x\n")
    git("add", ".", cwd=two)
    git("commit", "-qm", "remote commit", cwd=two)
    git("push", "-q", "origin", "main", cwd=two)

    monkeypatch.chdir(one)
    pull_operation(Namespace(branch=None))
    (one / "local.txt").write_text("y\n")
    git("add", ".", cwd=one)
    git("commit", "-qm", "local after pull", cwd=one)

    monkeypatch.setattr("pygitgo.utils.cli_io.confirm", lambda *a, **k: True)
    with pytest.raises(GitGoError, match="moved since the last pull"):
        abort_pull_conflict()


# ---------- bug 1: logout ----------

def _fake_key(env, monkeypatch):
    key = env / "home" / ".ssh" / "id_ed25519"
    key.write_text("PRIVATE KEY FOR OTHER SERVERS\n")
    Path(str(key) + ".pub").write_text("ssh-ed25519 AAAA\n")
    monkeypatch.setattr("pygitgo.auth.ssh_utils.get_ssh_key_path", lambda: key)
    return key


def test_logout_declined_keeps_key_and_identity(env, monkeypatch):
    from pygitgo.auth import manager

    key = _fake_key(env, monkeypatch)
    monkeypatch.setattr(manager, "confirm", lambda *a, **k: False)

    assert manager.logout() is False
    assert key.read_text().startswith("PRIVATE KEY")
    assert git("config", "--global", "user.name") == "Test User"


def test_logout_backs_up_key_and_keeps_identity_by_default_choice(env, monkeypatch):
    from pygitgo.auth import manager

    key = _fake_key(env, monkeypatch)
    answers = iter([True, False])  # remove key: yes, clear identity: no
    monkeypatch.setattr(manager, "confirm", lambda *a, **k: next(answers))

    assert manager.logout() is True
    assert not key.exists()
    backups = list(key.parent.glob("id_ed25519.gitgo-backup-*"))
    assert len(backups) == 2  # private + .pub
    assert any(b.read_text().startswith("PRIVATE KEY") for b in backups if not b.name.endswith(".pub"))
    assert git("config", "--global", "user.email") == "test@example.com"


# ---------- bug 5: output encoding ----------

def test_banner_does_not_crash_on_cp1252_stdout(monkeypatch):
    from pygitgo.utils import cli_io

    raw = io.BytesIO()
    fake = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", fake)

    cli_io.banner("Commit History", "Showing last 5 commits", required=True)
    fake.flush()

    out = raw.getvalue().decode("cp1252")
    assert "Commit History" in out
    assert cli_io.ok_mark() == "OK"

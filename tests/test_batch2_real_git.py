"""Real-git tests for the safety improvements (secret guard, undo backup, undo push guard, main-branch detection)."""
from argparse import Namespace
import io
import subprocess
import sys

import pytest

from pygitgo.exceptions import GitGoError


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / ".gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for k, v in (("user.name", "T"), ("user.email", "t@example.com"), ("init.defaultBranch", "main"), ("commit.gpgsign", "false")):
        git("config", "--global", k, v)
    return tmp_path


@pytest.fixture
def repo(env, monkeypatch):
    r = env / "repo"
    r.mkdir()
    git("init", "-q", cwd=r)
    (r / "app.py").write_text("print(1)\n")
    git("add", ".", cwd=r)
    git("commit", "-qm", "init", cwd=r)
    monkeypatch.chdir(r)
    return r


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


def answer(monkeypatch, choice):
    monkeypatch.setattr(sys, "stdin", FakeTTY())
    monkeypatch.setattr("builtins.input", lambda *_: choice)


# ---------- secret guard ----------

def test_commit_refuses_env_file_when_not_interactive(repo):
    from pygitgo.commands.git_core import git_commit
    (repo / ".env").write_text("SECRET_KEY=abc\n")
    (repo / "app.py").write_text("print(2)\n")

    with pytest.raises(GitGoError, match="look like secrets"):
        git_commit("update")

    assert git("diff", "--cached", "--name-only", cwd=repo) == ""  # nothing staged
    assert git("log", "--oneline", cwd=repo).count("\n") == 0       # no new commit


def test_commit_allows_secrets_with_explicit_flag(repo):
    from pygitgo.commands.git_core import git_commit
    (repo / ".env").write_text("SECRET_KEY=abc\n")
    assert git_commit("add env", allow_sensitive=True) is True
    assert ".env" in git("ls-tree", "-r", "--name-only", "HEAD", cwd=repo)


def test_commit_ignore_choice_gitignores_untracked_secret_and_commits_rest(repo, monkeypatch):
    from pygitgo.commands.git_core import git_commit
    (repo / ".env").write_text("SECRET_KEY=abc\n")
    (repo / "app.py").write_text("print(2)\n")
    answer(monkeypatch, "i")

    assert git_commit("update") is True

    tree = git("ls-tree", "-r", "--name-only", "HEAD", cwd=repo)
    assert ".env" not in tree and "app.py" in tree
    assert "/.env" in (repo / ".gitignore").read_text()


def test_commit_abort_choice_leaves_everything_untouched(repo, monkeypatch):
    from pygitgo.commands.git_core import git_commit
    (repo / "key.pem").write_text("-----BEGIN PRIVATE KEY-----\n")
    answer(monkeypatch, "a")

    with pytest.raises(GitGoError, match="Nothing was staged"):
        git_commit("add key")

    assert git("status", "--porcelain", cwd=repo) == "?? key.pem"


def test_commit_finds_secrets_inside_new_folders(repo):
    from pygitgo.commands.git_core import git_commit
    (repo / "config").mkdir()
    (repo / "config" / ".env").write_text("TOKEN=1\n")
    with pytest.raises(GitGoError, match="look like secrets"):
        git_commit("add config")


def test_commit_does_not_flag_env_example(repo):
    from pygitgo.commands.git_core import git_commit
    (repo / ".env.example").write_text("TOKEN=\n")
    assert git_commit("add example") is True


def test_commit_ignore_choice_with_only_a_tracked_secret_leaves_nothing_to_commit(repo, monkeypatch):
    from pygitgo.commands.git_core import git_commit
    (repo / ".env").write_text("A=1\n")
    git("add", "-f", ".env", cwd=repo)
    git("commit", "-qm", "oops tracked env", cwd=repo)
    (repo / ".env").write_text("A=2\n")
    answer(monkeypatch, "i")

    assert git_commit("change env") is False
    assert git("log", "-1", "--format=%s", cwd=repo) == "oops tracked env"


def test_picker_selected_secret_is_also_guarded(repo):
    from pygitgo.commands.git_core import git_commit
    (repo / ".env").write_text("A=1\n")
    git("add", ".env", cwd=repo)
    with pytest.raises(GitGoError, match="look like secrets"):
        git_commit("only env", skip_staging=True)


# ---------- undo changes backup ----------

def test_undo_changes_backs_up_and_state_can_restore(repo, monkeypatch):
    from pygitgo.commands.undo import undo_changes
    (repo / "app.py").write_text("print('edited')\n")
    (repo / "new file.txt").write_text("untracked work\n")
    monkeypatch.setattr("pygitgo.commands.undo.confirm", lambda *a, **k: True)

    assert undo_changes() is True

    assert (repo / "app.py").read_text() == "print(1)\n"
    assert not (repo / "new file.txt").exists()
    assert "GitGo undo-changes backup" in git("stash", "list", cwd=repo)

    git("stash", "pop", cwd=repo)
    assert (repo / "app.py").read_text() == "print('edited')\n"
    assert (repo / "new file.txt").read_text() == "untracked work\n"


def test_undo_changes_permanent_leaves_no_backup(repo, monkeypatch):
    from pygitgo.commands.undo import undo_changes
    (repo / "app.py").write_text("print('edited')\n")
    monkeypatch.setattr("pygitgo.commands.undo.confirm", lambda *a, **k: True)

    assert undo_changes(permanent=True) is True
    assert git("stash", "list", cwd=repo) == ""
    assert (repo / "app.py").read_text() == "print(1)\n"


def test_undo_changes_on_clean_tree_is_a_noop(repo):
    from pygitgo.commands.undo import undo_changes
    assert undo_changes() is False


# ---------- undo push guard ----------

@pytest.fixture
def pushed_repo(env, monkeypatch):
    remote = env / "remote.git"
    git("init", "-q", "--bare", "-b", "main", str(remote))
    r = env / "work"
    git("clone", "-q", str(remote), str(r))
    (r / "a.txt").write_text("1\n")
    git("add", ".", cwd=r)
    git("commit", "-qm", "first", cwd=r)
    git("push", "-q", "origin", "main", cwd=r)
    (r / "a.txt").write_text("2\n")
    git("commit", "-qam", "second", cwd=r)
    git("push", "-q", "origin", "main", cwd=r)
    monkeypatch.chdir(r)
    return remote, r


def test_undo_push_removes_only_the_last_pushed_commit(pushed_repo, monkeypatch):
    from pygitgo.commands.undo import undo_push
    remote, r = pushed_repo
    monkeypatch.setattr("pygitgo.commands.undo.confirm", lambda *a, **k: True)

    assert undo_push() is True
    assert git("log", "--format=%s", "main", cwd=remote) == "first"


def test_undo_push_refuses_when_local_has_unpushed_commits(pushed_repo, monkeypatch):
    from pygitgo.commands.undo import undo_push
    remote, r = pushed_repo
    (r / "b.txt").write_text("x\n")
    git("add", ".", cwd=r)
    git("commit", "-qm", "local only", cwd=r)
    monkeypatch.setattr("pygitgo.commands.undo.confirm", lambda *a, **k: True)

    with pytest.raises(GitGoError, match="never pushed"):
        undo_push()
    assert git("log", "--format=%s", "main", cwd=remote).splitlines() == ["second", "first"]  # remote untouched


# ---------- main-branch detection ----------

def test_get_main_branch_reads_local_origin_head_without_network(pushed_repo, monkeypatch):
    from pygitgo.commands import git_branch
    remote, r = pushed_repo
    git("remote", "set-head", "origin", "main", cwd=r)
    calls = []
    real = git_branch.run_command
    monkeypatch.setattr(git_branch, "run_command", lambda cmd, *a, **k: (calls.append(cmd), real(cmd, *a, **k))[1])

    assert git_branch.get_main_branch() == "main"
    assert ["git", "remote", "show", "origin"] not in calls


# ---------- push: typo'd branch name ----------

def test_suggest_branch_catches_typos_but_not_messages(repo):
    from pygitgo.commands.git_branch import suggest_branch
    git("branch", "-M", "main", cwd=repo)
    git("branch", "feature/login", cwd=repo)

    assert suggest_branch("mian") == "main"
    assert suggest_branch("feature/logn") == "feature/login"
    assert suggest_branch("fix the login bug") is None   # has spaces: a commit message
    assert suggest_branch("docs") is None                # not close to anything


def test_push_asks_before_treating_typo_as_commit_message(pushed_repo, monkeypatch):
    from pygitgo.commands import push as push_mod
    remote, r = pushed_repo
    (r / "c.txt").write_text("x\n")
    answer(monkeypatch, "y")
    asked = []
    monkeypatch.setattr(push_mod, "confirm", lambda prompt, **k: (asked.append(prompt), True)[1])

    push_mod.push_operation(Namespace(branch="mian", message=None, new=False, select=False, allow_sensitive=False))

    assert "Did you mean the branch 'main'" in asked[0]
    assert git("log", "-1", "--format=%s", "main", cwd=remote) == "chore: new changes applied"  # not "mian"


def test_push_declining_suggestion_keeps_old_behavior(pushed_repo, monkeypatch):
    from pygitgo.commands import push as push_mod
    remote, r = pushed_repo
    (r / "c.txt").write_text("x\n")
    answer(monkeypatch, "n")
    monkeypatch.setattr(push_mod, "confirm", lambda prompt, **k: False)

    push_mod.push_operation(Namespace(branch="mian", message=None, new=False, select=False, allow_sensitive=False))

    assert git("log", "-1", "--format=%s", "main", cwd=remote) == "mian"

import shutil
import subprocess
from argparse import Namespace
from pygitgo.commands.log import log_operation
from pygitgo.utils import platform as plat


def _repo(tmp_path, monkeypatch):
    env = {"GIT_AUTHOR_NAME": "A", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "A", "GIT_COMMITTER_EMAIL": "a@x"}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.chdir(tmp_path)
    run = lambda *a: subprocess.run(a, check=True, capture_output=True)
    run("git", "init", "-q")
    run("git", "config", "commit.gpgsign", "false")
    for msg in ("fix login bug", "add feature"):
        (tmp_path / msg.replace(" ", "_")).write_text(msg)
        run("git", "add", "-A")
        run("git", "commit", "-q", "-m", msg)


def test_log_grep_filters_real_history(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch)
    log_operation(Namespace(number=5, branch=None, author=None, since=None, grep="fix"))
    out = capsys.readouterr().out
    assert "fix login bug" in out and "add feature" not in out
    assert "grep: fix" in out


def test_log_author_filter_with_no_match(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch)
    log_operation(Namespace(number=5, branch=None, author="nobody", since=None, grep=None))
    assert "No commits match those filters" in capsys.readouterr().out


def test_copy_to_clipboard_returns_false_without_a_tool(mocker):
    mocker.patch.object(plat, "get_platform", return_value="linux")
    mocker.patch.object(plat.shutil, "which", return_value=None)
    assert plat.copy_to_clipboard("x") is False


def test_copy_to_clipboard_uses_first_available_tool(mocker):
    mocker.patch.object(plat, "get_platform", return_value="linux")
    mocker.patch.object(plat.shutil, "which", side_effect=lambda n: "/usr/bin/xclip" if n == "xclip" else None)
    run = mocker.patch.object(plat.subprocess, "run")
    assert plat.copy_to_clipboard("ssh-ed25519 AAAA") is True
    assert run.call_args[0][0][0] == "xclip"
    assert run.call_args[1]["input"] == b"ssh-ed25519 AAAA"


def _git(*a, cwd=None):
    return subprocess.run(a, check=True, capture_output=True, text=True, cwd=cwd)


def _repo_with_remote(tmp_path, monkeypatch):
    for k, v in {"GIT_AUTHOR_NAME": "A", "GIT_AUTHOR_EMAIL": "a@x", "GIT_COMMITTER_NAME": "A", "GIT_COMMITTER_EMAIL": "a@x"}.items():
        monkeypatch.setenv(k, v)
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    work.mkdir()
    _git("git", "init", "-q", "--bare", str(remote))
    monkeypatch.chdir(work)
    _git("git", "init", "-q", "-b", "main")
    _git("git", "config", "commit.gpgsign", "false")
    (work / "a").write_text("1")
    _git("git", "add", "-A")
    _git("git", "commit", "-q", "-m", "first")
    _git("git", "remote", "add", "origin", str(remote))
    _git("git", "push", "-q", "-u", "origin", "main")
    return work


def test_log_marks_unpushed_commits_and_shows_refs(tmp_path, monkeypatch, capsys):
    work = _repo_with_remote(tmp_path, monkeypatch)
    (work / "b").write_text("2")
    _git("git", "add", "-A")
    _git("git", "commit", "-q", "-m", "local only")
    _git("git", "tag", "v1")
    log_operation(Namespace(number=5, branch=None, author=None, since=None, grep=None, graph=False))
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if "local only" in l or "first" in l]
    local = next(l for l in lines if "local only" in l)
    first = next(l for l in lines if "first" in l)
    assert "[unpushed]" in local and "v1" in local and "HEAD -> main" in local
    assert "[unpushed]" not in first and "origin/main" in first
    assert "1 commit(s) not pushed yet" in out


def test_log_everything_pushed_shows_no_warning(tmp_path, monkeypatch, capsys):
    _repo_with_remote(tmp_path, monkeypatch)
    log_operation(Namespace(number=5, branch=None, author=None, since=None, grep=None, graph=False))
    out = capsys.readouterr().out
    assert "[unpushed]" not in out and "not pushed yet" not in out


def test_log_without_upstream_does_not_crash_or_mark(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch)
    log_operation(Namespace(number=5, branch=None, author=None, since=None, grep=None, graph=False))
    out = capsys.readouterr().out
    assert "add feature" in out and "[unpushed]" not in out


def test_log_graph_shows_branch_structure(tmp_path, monkeypatch, capsys):
    work = _repo_with_remote(tmp_path, monkeypatch)
    _git("git", "checkout", "-q", "-b", "feat")
    (work / "f").write_text("f")
    _git("git", "add", "-A")
    _git("git", "commit", "-q", "-m", "on feat")
    _git("git", "checkout", "-q", "main")
    (work / "m").write_text("m")
    _git("git", "add", "-A")
    _git("git", "commit", "-q", "-m", "on main")
    _git("git", "merge", "-q", "--no-ff", "-m", "merge feat", "feat")
    log_operation(Namespace(number=10, branch=None, author=None, since=None, grep=None, graph=True))
    out = capsys.readouterr().out
    assert "merge feat" in out and "on feat" in out and "on main" in out
    assert any(l.lstrip().startswith("*") for l in out.splitlines())
    assert any(c in out for c in ("|\\", "|/", "|"))

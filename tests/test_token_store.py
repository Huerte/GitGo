import os
import subprocess
import pytest
from pygitgo.utils import token_store


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Isolated HOME with no credential helper configured, so the file fallback is used."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / ".gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_ASKPASS", "")
    monkeypatch.setenv("SSH_ASKPASS", "")
    monkeypatch.setenv("GITGO_NO_CREDENTIAL_HELPER", "1")  # file fallback only, unless a test opts in
    monkeypatch.setattr(token_store, "_helper_broken", False)
    return tmp_path


def test_round_trip_without_a_helper_uses_a_private_file(home):
    assert token_store.save_token("ghp_abc") == "file"
    assert token_store.load_token() == "ghp_abc"
    if os.name != "nt":
        assert oct(token_store._token_file().stat().st_mode & 0o777) == "0o600"


def test_token_is_never_written_to_gitconfig(home):
    token_store.save_token("ghp_secret")
    cfg = home / ".gitconfig"
    assert not cfg.exists() or "ghp_secret" not in cfg.read_text()


def test_delete_removes_everything(home):
    token_store.save_token("ghp_abc")
    token_store.delete_token()
    assert token_store.load_token() == ""
    assert not token_store._token_file().exists()


def test_legacy_gitconfig_token_is_migrated_and_removed(home):
    subprocess.run(["git", "config", "--global", "gitgo.github-token", "ghp_old"], check=True)
    assert token_store.load_token() == "ghp_old"
    cfg = (home / ".gitconfig").read_text()
    assert "ghp_old" not in cfg and "github-token" not in cfg
    assert token_store._file_load() == "ghp_old"
    assert token_store.load_token() == "ghp_old"


def test_credential_helper_is_preferred_when_it_stores(home, monkeypatch):
    monkeypatch.delenv("GITGO_NO_CREDENTIAL_HELPER")
    monkeypatch.chdir(home)  # a mangled relative path must land in the temp dir, never in the repo
    store = home / "creds"
    # git runs the helper string through a shell, which eats backslashes: use forward slashes.
    subprocess.run(["git", "config", "--global", "credential.helper", f"store --file={store.as_posix()}"], check=True)
    assert token_store.save_token("ghp_helper") == "credential-helper"
    assert not token_store._token_file().exists()
    assert token_store.load_token() == "ghp_helper"
    assert "token.gitgo.invalid" in store.read_text()
    token_store.delete_token()
    assert token_store.load_token() == ""


def test_overwrite_replaces_old_token(home):
    token_store.save_token("first")
    token_store.save_token("second")
    assert token_store.load_token() == "second"


def test_hanging_helper_is_abandoned_quickly_and_file_fallback_works(home, monkeypatch, tmp_path):
    """A helper that never answers must not freeze GitGo (or the test suite)."""
    import sys, time
    if os.name == "nt":
        pytest.skip("uses a POSIX shell script as the fake helper")
    monkeypatch.delenv("GITGO_NO_CREDENTIAL_HELPER")
    monkeypatch.setattr(token_store, "_HELPER_TIMEOUT", 1)
    hang = tmp_path / "git-credential-hang"
    hang.write_text("#!/bin/sh\nsleep 60\n")
    hang.chmod(0o755)
    subprocess.run(["git", "config", "--global", "credential.helper", f"!{hang}"], check=True)

    start = time.monotonic()
    assert token_store.save_token("ghp_hang") == "file"
    assert token_store.load_token() == "ghp_hang"
    assert time.monotonic() - start < 10
    assert token_store._helper_broken is True


def test_blocking_askpass_env_is_neutralised(home, monkeypatch, tmp_path):
    """GIT_ASKPASS from the environment (VS Code sets one) must not be invoked."""
    if os.name == "nt":
        pytest.skip("uses a POSIX shell script as the fake askpass")
    import time
    marker = tmp_path / "askpass-ran"
    script = tmp_path / "askpass.sh"
    script.write_text(f"#!/bin/sh\ntouch {marker}\nsleep 30\n")
    script.chmod(0o755)
    monkeypatch.setenv("GIT_ASKPASS", str(script))
    monkeypatch.delenv("GITGO_NO_CREDENTIAL_HELPER")
    start = time.monotonic()
    token_store.save_token("ghp_x")
    assert time.monotonic() - start < 8
    assert not marker.exists()

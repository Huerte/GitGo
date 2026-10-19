import os
import subprocess
from pathlib import Path
import pytest
from pygitgo.auth import ssh_utils as su


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / ".gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    (tmp_path / ".ssh").mkdir()
    monkeypatch.setattr(su, "ensure_ssh_agent", lambda *a, **k: True)
    return tmp_path


def _gitconfig(*args):
    return subprocess.run(["git", "config", "--global", *args], capture_output=True, text=True)


def _legacy(home, signing=True):
    old = home / ".ssh" / "id_ed25519"
    old.write_text("PRIVATE")
    (home / ".ssh" / "id_ed25519.pub").write_text("ssh-ed25519 AAAA me")
    if signing:
        _gitconfig("user.signingkey", str(old))
    return old


def test_new_key_path_is_dedicated(home):
    assert su.get_ssh_key_path() == home / ".ssh" / "gitgo_ed25519"


def test_migration_copies_and_repoints_signing(home):
    old = _legacy(home)
    assert su.migrate_legacy_key() is True
    new = su.get_ssh_key_path()
    assert new.read_text() == "PRIVATE"
    assert (new.parent / "gitgo_ed25519.pub").read_text() == "ssh-ed25519 AAAA me"
    assert old.read_text() == "PRIVATE" and old.exists()  # original untouched
    assert _gitconfig("user.signingkey").stdout.strip() == str(new)
    if os.name != "nt":
        assert oct(new.stat().st_mode & 0o777) == "0o600"
    assert "gitgo_ed25519" in (home / ".ssh" / "config").read_text()


def test_migration_ignores_keys_gitgo_did_not_create(home):
    _legacy(home, signing=False)
    assert su.migrate_legacy_key() is False
    assert not su.get_ssh_key_path().exists()


def test_migration_ignores_signing_key_pointing_elsewhere(home):
    _legacy(home, signing=False)
    _gitconfig("user.signingkey", str(home / ".ssh" / "work_key"))
    assert su.migrate_legacy_key() is False


def test_migration_never_overwrites_existing_gitgo_key(home):
    _legacy(home)
    su.get_ssh_key_path().write_text("MINE")
    assert su.migrate_legacy_key() is False
    assert su.get_ssh_key_path().read_text() == "MINE"


def test_migration_is_noop_with_nothing_to_migrate(home):
    assert su.migrate_legacy_key() is False


def test_config_block_added_at_top_and_user_config_preserved(home):
    cfg = home / ".ssh" / "config"
    cfg.write_text("Host work\n    HostName w.example\n")
    su.ensure_ssh_config(su.get_ssh_key_path())
    text = cfg.read_text()
    assert text.startswith("# >>> gitgo")
    assert "Host work\n    HostName w.example\n" in text
    assert "IdentitiesOnly" not in text  # other keys must keep working


def test_config_block_is_idempotent_and_updates_in_place(home):
    cfg = home / ".ssh" / "config"
    su.ensure_ssh_config(Path("/a/key"))
    su.ensure_ssh_config(Path("/b/key"))
    text = cfg.read_text()
    assert text.count("# >>> gitgo") == 1
    assert "/b/key" in text and "/a/key" not in text


def test_config_block_removal_restores_user_content(home):
    cfg = home / ".ssh" / "config"
    original = "Host work\n    HostName w.example\n"
    cfg.write_text(original)
    su.ensure_ssh_config(su.get_ssh_key_path())
    su.remove_ssh_config_block()
    assert cfg.read_text().strip() == original.strip()


def test_remove_block_without_config_file_is_safe(home):
    su.remove_ssh_config_block()


def test_sanitize_signing_config_triggers_migration(home):
    from pygitgo.auth.account import sanitize_signing_config
    _legacy(home)
    sanitize_signing_config()
    assert su.get_ssh_key_path().exists()

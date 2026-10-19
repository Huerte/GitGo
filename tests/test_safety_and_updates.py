import json
import sys
from datetime import datetime

import pytest

from pygitgo.utils.safety import is_sensitive, find_sensitive
from pygitgo.utils import update_checker


@pytest.mark.parametrize("path", [
    ".env", ".env.local", ".env.production", "config/.env", "server.pem", "deploy.key", "id_rsa",
    "id_ed25519", "credentials.json", "service-account-prod.json", "dir\\secrets.yml", ".netrc",
])
def test_sensitive_names_are_flagged(path):
    assert is_sensitive(path)


@pytest.mark.parametrize("path", [
    ".env.example", ".env.sample", "env.py", "id_ed25519.pub", "README.md", "src/keyboard.py", "monkey.txt",
])
def test_normal_names_are_not_flagged(path):
    assert not is_sensitive(path)


def test_find_sensitive_filters_list():
    assert find_sensitive(["a.py", ".env", "b/key.pem"]) == [".env", "b/key.pem"]


# ---------- update hints ----------

@pytest.mark.parametrize("prefix,exe,expected", [
    ("/home/u/.local/pipx/venvs/pygitgo", "/home/u/.local/pipx/venvs/pygitgo/bin/python", "pipx upgrade pygitgo"),
    ("C:\\Users\\u\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Huerte.GitGo", "C:\\Users\\u\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Huerte.GitGo\\gitgo.exe", "winget upgrade Huerte.GitGo"),
    ("/home/u/.gitgo/venv", "/home/u/.gitgo/venv/bin/python", "re-run the GitGo install script"),
    ("/usr", "/usr/bin/python3", "pip install --upgrade pygitgo"),
])
def test_upgrade_command_matches_install_method(monkeypatch, prefix, exe, expected):
    monkeypatch.setattr(sys, "prefix", prefix)
    monkeypatch.setattr(sys, "executable", exe)
    assert update_checker.upgrade_command() == expected


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(update_checker, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(update_checker, "CACHE_FILE", tmp_path / "update_check.json")
    return tmp_path / "update_check.json"


def test_cached_notice_shows_once_per_day_without_network(cache, monkeypatch):
    cache.write_text(json.dumps({"notified_version": "9.9.9"}))
    monkeypatch.setattr(update_checker, "get_latest_version", lambda: pytest.fail("must not hit the network"))

    first = update_checker.cached_update_notice("1.0.0")
    assert first and "9.9.9" in first and "Run:" in first
    assert update_checker.cached_update_notice("1.0.0") is None  # already shown today

    data = json.loads(cache.read_text())
    data["last_notice"] = "2000-01-01"
    cache.write_text(json.dumps(data))
    assert update_checker.cached_update_notice("1.0.0") is not None  # a new day


def test_cached_notice_silent_when_up_to_date_or_no_cache(cache):
    assert update_checker.cached_update_notice("1.0.0") is None
    cache.write_text(json.dumps({"notified_version": "1.0.0"}))
    assert update_checker.cached_update_notice("1.0.0") is None
    assert update_checker.cached_update_notice("2.0.0") is None

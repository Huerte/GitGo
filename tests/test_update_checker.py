from pygitgo.utils.update_checker import (
    read_cache, write_cache, should_check, get_latest_version,
    parse_version, check_for_updates, check_for_updates_background
)
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import json


def test_read_cache_empty(tmp_path, mocker):
    mocker.patch("pygitgo.utils.update_checker.CACHE_FILE", tmp_path / "missing.json")
    assert read_cache() == {}


def test_read_cache_valid(tmp_path, mocker):
    cache_file = tmp_path / "update_check.json"
    cache_file.write_text(json.dumps({"last_check": "2026-01-01T00:00:00"}))
    mocker.patch("pygitgo.utils.update_checker.CACHE_FILE", cache_file)
    result = read_cache()
    assert result["last_check"] == "2026-01-01T00:00:00"


def test_read_cache_corrupted(tmp_path, mocker):
    cache_file = tmp_path / "update_check.json"
    cache_file.write_text("not json")
    mocker.patch("pygitgo.utils.update_checker.CACHE_FILE", cache_file)
    assert read_cache() == {}


def test_write_cache(tmp_path, mocker):
    cache_file = tmp_path / "update_check.json"
    mocker.patch("pygitgo.utils.update_checker.CACHE_DIR", tmp_path)
    mocker.patch("pygitgo.utils.update_checker.CACHE_FILE", cache_file)
    write_cache({"last_check": "2026-01-01T00:00:00"})
    result = json.loads(cache_file.read_text())
    assert result["last_check"] == "2026-01-01T00:00:00"


def test_should_check_no_cache(mocker):
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={})
    assert should_check() is True


def test_should_check_expired(mocker):
    old_date = (datetime.now() - timedelta(days=8)).isoformat()
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={"last_check": old_date})
    assert should_check() is True


def test_should_check_still_valid(mocker):
    recent_date = (datetime.now() - timedelta(days=1)).isoformat()
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={"last_check": recent_date})
    assert should_check() is False


def test_should_check_invalid_date(mocker):
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={"last_check": "not-a-date"})
    assert should_check() is True


def test_parse_version_standard():
    assert parse_version("1.5.0") == [1, 5, 0]


def test_parse_version_short():
    assert parse_version("2.0") == [2, 0, 0]


def test_parse_version_comparison():
    assert parse_version("1.6.0") > parse_version("1.5.0")
    assert parse_version("2.0.0") > parse_version("1.9.9")
    assert parse_version("1.5.0") == parse_version("1.5.0")


def test_get_latest_version_success(mocker):
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"info": {"version": "1.6.0"}}).encode("utf-8")
    fake_response.__enter__ = lambda s: s
    fake_response.__exit__ = MagicMock(return_value=False)
    mocker.patch("pygitgo.utils.update_checker.urllib.request.urlopen", return_value=fake_response)
    assert get_latest_version() == "1.6.0"


def test_get_latest_version_network_failure(mocker):
    mocker.patch("pygitgo.utils.update_checker.urllib.request.urlopen", side_effect=Exception("timeout"))
    assert get_latest_version() is None


def test_check_for_updates_skips_when_cached(mocker):
    mocker.patch("pygitgo.utils.update_checker.should_check", return_value=False)
    fake_get = mocker.patch("pygitgo.utils.update_checker.get_latest_version")
    check_for_updates("1.5.0")
    fake_get.assert_not_called()


def test_check_for_updates_no_update_available(mocker):
    mocker.patch("pygitgo.utils.update_checker.should_check", return_value=True)
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={})
    mocker.patch("pygitgo.utils.update_checker.write_cache")
    mocker.patch("pygitgo.utils.update_checker.get_latest_version", return_value="1.5.0")
    fake_warning = mocker.patch("pygitgo.utils.update_checker.warning")
    check_for_updates("1.5.0")
    fake_warning.assert_not_called()


def test_check_for_updates_newer_version_available(mocker):
    mocker.patch("pygitgo.utils.update_checker.should_check", return_value=True)
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={})
    mocker.patch("pygitgo.utils.update_checker.write_cache")
    mocker.patch("pygitgo.utils.update_checker.get_latest_version", return_value="2.0.0")
    fake_warning = mocker.patch("pygitgo.utils.update_checker.warning")
    fake_info = mocker.patch("pygitgo.utils.update_checker.info")
    check_for_updates("1.5.0")
    fake_warning.assert_called_with("GitGo update available: 1.5.0 -> 2.0.0")
    fake_info.assert_called_with("Run: pip install --upgrade pygitgo")


def test_check_for_updates_older_version_on_pypi(mocker):
    mocker.patch("pygitgo.utils.update_checker.should_check", return_value=True)
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={})
    mocker.patch("pygitgo.utils.update_checker.write_cache")
    mocker.patch("pygitgo.utils.update_checker.get_latest_version", return_value="1.4.0")
    fake_warning = mocker.patch("pygitgo.utils.update_checker.warning")
    check_for_updates("1.5.0")
    fake_warning.assert_not_called()


def test_check_for_updates_pypi_returns_none(mocker):
    mocker.patch("pygitgo.utils.update_checker.should_check", return_value=True)
    mocker.patch("pygitgo.utils.update_checker.read_cache", return_value={})
    mocker.patch("pygitgo.utils.update_checker.write_cache")
    mocker.patch("pygitgo.utils.update_checker.get_latest_version", return_value=None)
    fake_warning = mocker.patch("pygitgo.utils.update_checker.warning")
    check_for_updates("1.5.0")
    fake_warning.assert_not_called()


def test_check_for_updates_background_starts_thread(mocker):
    fake_thread = MagicMock()
    mocker.patch("pygitgo.utils.update_checker.threading.Thread", return_value=fake_thread)
    check_for_updates_background("1.5.0")
    fake_thread.start.assert_called_once()

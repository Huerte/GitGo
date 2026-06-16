from pygitgo.auth.manager import login, logout
from pathlib import Path
from unittest.mock import call
import pytest


def test_login_already_logged_in_with_managed_key(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    fake_check = mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=True)
    
    mock_key = mocker.MagicMock(spec=Path)
    mock_key.exists.return_value = True
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=mock_key)
    
    fake_config_signing = mocker.patch("pygitgo.auth.manager._configure_ssh_signing")
    fake_ensure = mocker.patch("pygitgo.auth.account.ensure_user_configure")
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_github_username", return_value="GithubUser")
    fake_success = mocker.patch("pygitgo.auth.manager.success")

    result = login()

    assert result is True
    fake_check.assert_called_once_with(ok_text="Already logged in via GitGo.", fail_text="Not connected to GitHub.")
    fake_config_signing.assert_called_once_with(mock_key)
    fake_ensure.assert_called_once_with(default_username="GithubUser")
    fake_success.assert_not_called()


def test_login_already_logged_in_with_unmanaged_key(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    fake_check = mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=True)
    
    mock_key = mocker.MagicMock(spec=Path)
    mock_key.exists.return_value = False
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=mock_key)
    
    fake_warning = mocker.patch("pygitgo.auth.manager.warning")
    fake_info = mocker.patch("pygitgo.auth.manager.info")

    result = login()

    assert result is True
    fake_check.assert_called_once_with(ok_text="GitHub connection verified.", fail_text="Not connected to GitHub.")
    assert fake_warning.call_count == 2
    assert fake_info.call_count == 2


def test_login_new_user_success(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    fake_check = mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", side_effect=[False, True])
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.manager.open_url")
    mocker.patch("pygitgo.auth.manager.success")
    mocker.patch("builtins.input", side_effect=["test@example.com", "", ""])
    mocker.patch("pygitgo.auth.manager.ssh_utils.generate_ssh_key", return_value=Path("mock_key"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("mock_key"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.ensure_ssh_agent")
    
    mocker.patch("builtins.open", mocker.mock_open(read_data="ssh-rsa AAAAB3NzaC1yc2E..."))
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_github_username", return_value="GithubUser")
    fake_ensure = mocker.patch("pygitgo.auth.account.ensure_user_configure", return_value=True)

    result = login()

    assert result is True
    fake_ensure.assert_called_once_with(default_email="test@example.com", default_username="GithubUser")
    fake_check.assert_has_calls([
        call(ok_text="GitHub connection verified.", fail_text="Not connected to GitHub."),
        call(ok_text="Login successful. You are connected.", fail_text="SSH key not recognised by GitHub.")
    ])


def test_login_new_user_verification_fails(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    fake_check = mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=False)
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.manager.success")
    mocker.patch("pygitgo.auth.manager.error")
    mocker.patch("builtins.input", side_effect=["test@example.com", "", ""])
    mocker.patch("pygitgo.auth.manager.ssh_utils.generate_ssh_key", return_value=Path("mock_key"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("mock_key"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.ensure_ssh_agent")
    mocker.patch("pygitgo.auth.manager.open_url")
    mocker.patch("builtins.open", mocker.mock_open(read_data="ssh-rsa AAAAB3NzaC1yc2E..."))
    
    mocker.patch("pygitgo.auth.manager.get_platform", return_value="windows")

    result = login()

    assert result is False
    fake_check.assert_has_calls([
        call(ok_text="GitHub connection verified.", fail_text="Not connected to GitHub."),
        call(ok_text="Login successful. You are connected.", fail_text="SSH key not recognised by GitHub.")
    ])


def test_login_new_user_verification_fails_linux(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    fake_check = mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=False)
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.manager.success")
    mocker.patch("pygitgo.auth.manager.error")
    mocker.patch("builtins.input", side_effect=["test@example.com", "", ""])
    mocker.patch("pygitgo.auth.manager.ssh_utils.generate_ssh_key", return_value=Path("mock_key"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("mock_key"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.ensure_ssh_agent")
    mocker.patch("pygitgo.auth.manager.open_url")
    mocker.patch("builtins.open", mocker.mock_open(read_data="ssh-rsa AAAAB3NzaC1yc2E..."))
    
    mocker.patch("pygitgo.auth.manager.get_platform", return_value="linux")

    result = login()

    assert result is False
    fake_check.assert_has_calls([
        call(ok_text="GitHub connection verified.", fail_text="Not connected to GitHub."),
        call(ok_text="Login successful. You are connected.", fail_text="SSH key not recognised by GitHub.")
    ])


def test_logout_not_logged_in(mocker):
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("non_existent_key"))
    mocker.patch.object(Path, "exists", return_value=False)
    fake_warning = mocker.patch("pygitgo.auth.manager.warning")

    result = logout()

    assert result is False
    fake_warning.assert_called_once_with("You are already logged out (no keys found).")


def test_logout_success(mocker):
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("mock_key"))
    mocker.patch.object(Path, "exists", return_value=True)
    fake_remove = mocker.patch("os.remove")
    fake_path_exists = mocker.patch("os.path.exists", return_value=True)
    fake_run = mocker.patch("pygitgo.auth.manager.run_command")
    fake_success = mocker.patch("pygitgo.auth.manager.success")

    result = logout()

    assert result is True
    assert fake_remove.call_count == 2
    fake_run.assert_any_call(["git", "config", "--global", "--unset-all", "user.name"])
    fake_run.assert_any_call(["git", "config", "--global", "--unset-all", "user.email"])
    fake_success.assert_called_once_with("User successfully logout")

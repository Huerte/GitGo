from pygitgo.auth.manager import login, logout
from unittest.mock import call
from pathlib import Path


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


def test_login_unmanaged_key_declined_leaves_everything_alone(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    fake_check = mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=True)
    mock_key = mocker.MagicMock(spec=Path)
    mock_key.exists.return_value = False
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=mock_key)
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.manager.confirm", return_value=False)
    gen = mocker.patch("pygitgo.auth.manager.ssh_utils.generate_ssh_key")

    assert login() is True
    fake_check.assert_called_once_with(ok_text="GitHub connection verified.", fail_text="Not connected to GitHub.")
    gen.assert_not_called()


def test_login_unmanaged_key_accepted_adds_gitgo_key(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", side_effect=[True, True])
    mock_key = mocker.MagicMock(spec=Path)
    mock_key.exists.return_value = False
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=mock_key)
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.manager.confirm", return_value=True)
    mocker.patch("pygitgo.auth.device_flow.is_available", return_value=False)
    manual = mocker.patch("pygitgo.auth.manager._manual_login", return_value=True)
    assert login() is True
    manual.assert_called_once_with()


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
    mocker.patch("pygitgo.auth.manager.confirm", return_value=True)
    fake_backup = mocker.patch("pygitgo.auth.manager._backup_key", return_value=Path("mock_key.bak"))
    mocker.patch("pygitgo.auth.manager.get_user", return_value=("Name", "me@example.com"))
    fake_run = mocker.patch("pygitgo.auth.manager.run_command")
    fake_success = mocker.patch("pygitgo.auth.manager.success")

    result = logout()

    assert result is True
    fake_backup.assert_called_once()
    fake_run.assert_any_call(["git", "config", "--global", "--unset-all", "user.name"], loading_msg="Clearing Git username...", ok_text="Git username cleared.")
    fake_run.assert_any_call(["git", "config", "--global", "--unset-all", "user.email"], loading_msg="Clearing Git email...", ok_text="Git email cleared.")
    fake_success.assert_called_with("User successfully logged out.")


def test_logout_declined_changes_nothing(mocker):
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("mock_key"))
    mocker.patch.object(Path, "exists", return_value=True)
    mocker.patch("pygitgo.auth.manager.confirm", return_value=False)
    fake_backup = mocker.patch("pygitgo.auth.manager._backup_key")
    fake_run = mocker.patch("pygitgo.auth.manager.run_command")

    assert logout() is False
    fake_backup.assert_not_called()
    fake_run.assert_not_called()


def test_login_uses_device_flow_when_available_and_interactive(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=False)
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("nokey"))
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.device_flow.is_available", return_value=True)
    mocker.patch("pygitgo.auth.manager.sys.stdin.isatty", return_value=True)
    dev = mocker.patch("pygitgo.auth.manager._device_login", return_value=True)
    manual = mocker.patch("pygitgo.auth.manager._manual_login")
    assert login() is True
    dev.assert_called_once_with()
    manual.assert_not_called()


def test_login_falls_back_to_manual_when_device_flow_gives_up(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=False)
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("nokey"))
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.device_flow.is_available", return_value=True)
    mocker.patch("pygitgo.auth.manager.sys.stdin.isatty", return_value=True)
    mocker.patch("pygitgo.auth.manager._device_login", return_value=None)
    manual = mocker.patch("pygitgo.auth.manager._manual_login", return_value=True)
    assert login() is True
    manual.assert_called_once_with()


def test_login_skips_device_flow_when_not_interactive(mocker):
    mocker.patch("pygitgo.auth.account.sanitize_signing_config")
    mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=False)
    mocker.patch("pygitgo.auth.manager.ssh_utils.get_ssh_key_path", return_value=Path("nokey"))
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.device_flow.is_available", return_value=True)
    mocker.patch("pygitgo.auth.manager.sys.stdin.isatty", return_value=False)
    dev = mocker.patch("pygitgo.auth.manager._device_login")
    mocker.patch("pygitgo.auth.manager._manual_login", return_value=True)
    login()
    dev.assert_not_called()


def test_device_login_happy_path_registers_key_and_configures(mocker):
    from pygitgo.auth import manager, device_flow
    mocker.patch.object(device_flow, "start", return_value={"user_code": "ABCD-1234", "verification_uri": "https://github.com/login/device"})
    mocker.patch.object(device_flow, "wait_for_token", return_value="tok")
    mocker.patch.object(device_flow, "fetch_identity", return_value=("octo", "octo@example.com"))
    upload = mocker.patch.object(device_flow, "upload_keys")
    mocker.patch("builtins.input", return_value="")
    mocker.patch("pygitgo.auth.manager.open_url")
    mocker.patch("pygitgo.auth.manager.copy_to_clipboard", return_value=True)
    mocker.patch("pygitgo.auth.manager.write")
    mocker.patch("pygitgo.auth.manager.info")
    mocker.patch("pygitgo.auth.manager.success")
    gen = mocker.patch("pygitgo.auth.manager.ssh_utils.generate_ssh_key", return_value=Path("k"))
    mocker.patch("builtins.open", mocker.mock_open(read_data="ssh-ed25519 AAAA octo@example.com\n"))
    mocker.patch("pygitgo.auth.manager.ssh_utils.check_connection", return_value=True)
    mocker.patch("pygitgo.auth.manager._configure_ssh_signing")
    ensure = mocker.patch("pygitgo.auth.account.ensure_user_configure", return_value=True)

    assert manager._device_login() is True
    gen.assert_called_once_with(email="octo@example.com")
    assert upload.call_args[0][0] == "tok"
    assert upload.call_args[0][1] == "ssh-ed25519 AAAA octo@example.com"
    ensure.assert_called_once_with(default_email="octo@example.com", default_username="octo")


def test_device_login_denied_returns_none_for_fallback(mocker):
    from pygitgo.auth import manager, device_flow
    mocker.patch.object(device_flow, "start", return_value={"user_code": "X", "verification_uri": "u"})
    mocker.patch.object(device_flow, "wait_for_token", side_effect=device_flow.DeviceFlowError("canceled"))
    mocker.patch("builtins.input", return_value="")
    for name in ("open_url", "copy_to_clipboard", "write", "info", "success", "warning"):
        mocker.patch(f"pygitgo.auth.manager.{name}")
    gen = mocker.patch("pygitgo.auth.manager.ssh_utils.generate_ssh_key")
    assert manager._device_login() is None
    gen.assert_not_called()

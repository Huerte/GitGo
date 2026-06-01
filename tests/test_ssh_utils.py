import pytest
from pathlib import Path
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.auth.ssh_utils import (
    ensure_github_known_host, check_connection, get_github_username,
    get_ssh_key_path, generate_ssh_key, open_github_settings,
    convert_https_to_ssh, is_ssh_url
)


def test_ensure_github_known_host_already_exists(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data="github.com ssh-rsa AAA..."))
    fake_run = mocker.patch("pygitgo.auth.ssh_utils.run_command")

    ensure_github_known_host()

    fake_run.assert_not_called()


def test_ensure_github_known_host_not_exists(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pathlib.Path.mkdir")
    mock_file = mocker.patch("builtins.open", mocker.mock_open())
    
    # Mock return value of run_command as a completed process
    mock_process = mocker.MagicMock()
    mock_process.stdout = "github.com ssh-rsa AAA...\n"
    fake_run = mocker.patch("pygitgo.auth.ssh_utils.run_command", return_value=mock_process)
    mocker.patch("pygitgo.auth.ssh_utils.info")
    mocker.patch("pygitgo.auth.ssh_utils.success")

    ensure_github_known_host()

    fake_run.assert_called_once_with(["ssh-keyscan", "-H", "github.com"], return_complete=True)
    mock_file().write.assert_any_call("github.com ssh-rsa AAA...\n")


def test_check_connection_success(mocker):
    mocker.patch("pygitgo.auth.ssh_utils.ensure_github_known_host")
    mocker.patch("pygitgo.auth.ssh_utils._get_github_ssh_response", return_value="Hi user! You've successfully authenticated.")

    result = check_connection()
    assert result is True


def test_check_connection_failure(mocker):
    mocker.patch("pygitgo.auth.ssh_utils.ensure_github_known_host")
    mocker.patch("pygitgo.auth.ssh_utils._get_github_ssh_response", return_value="Permission denied.")

    result = check_connection()
    assert result is False


def test_get_github_username_success(mocker):
    mocker.patch("pygitgo.auth.ssh_utils._get_github_ssh_response", return_value="Hi Alice! You've successfully authenticated.")
    assert get_github_username() == "Alice"


def test_get_github_username_failure(mocker):
    mocker.patch("pygitgo.auth.ssh_utils._get_github_ssh_response", return_value="Permission denied.")
    assert get_github_username() is None


def test_generate_ssh_key_invalid_email():
    with pytest.raises(GitGoError) as exc_info:
        generate_ssh_key("invalid-email")
    assert "Invalid email address" in str(exc_info.value)


def test_generate_ssh_key_success(mocker):
    mocker.patch("pygitgo.auth.ssh_utils.get_ssh_key_path", return_value=Path("mock_key"))
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pathlib.Path.mkdir")
    fake_run = mocker.patch("pygitgo.auth.ssh_utils.run_command")

    key_path = generate_ssh_key("test@example.com")

    assert key_path == Path("mock_key")
    fake_run.assert_any_call(
        command=[
            "ssh-keygen",
            "-t", "ed25519",
            "-C", "test@example.com",
            "-f", "mock_key",
            "-N", ""
        ]
    )
    fake_run.assert_any_call(["ssh-add", "mock_key"])


def test_convert_https_to_ssh():
    assert convert_https_to_ssh("https://github.com/user/repo") == "git@github.com:user/repo.git"
    assert convert_https_to_ssh("https://github.com/user/repo.git") == "git@github.com:user/repo.git"
    assert convert_https_to_ssh("git@github.com:user/repo.git") is None


def test_is_ssh_url():
    assert is_ssh_url("git@github.com:user/repo.git") is True
    assert is_ssh_url("https://github.com/user/repo") is False


@pytest.mark.parametrize("url", [
    "git@github.com:Huerte/GitGo.git",
    "git@gitlab.com:Company/App.git"
])
def test_is_ssh_url_valid(url):
    result = is_ssh_url(url)
    assert result is True


@pytest.mark.parametrize("url", [
    "https://github.com/Huerte/GitGo",
    "hello-world",
    ""
])
def test_is_ssh_url_invalid(url):
    result = is_ssh_url(url)
    assert result is False


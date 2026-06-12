from unittest.mock import patch, MagicMock
from pygitgo.exceptions import GitGoError
from pygitgo.commands.repo import (
    _get_github_token,
    create_github_repo,
    repo_operation,
    _clear_saved_token,
)
import urllib.error
import pytest


@patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
def test_get_github_token_env():
    assert _get_github_token() == "test-token"


@patch.dict("os.environ", {}, clear=True)
@patch("subprocess.run")
def test_get_github_token_gh_cli(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout=" cli-token ")
    assert _get_github_token() == "cli-token"


@patch.dict("os.environ", {}, clear=True)
@patch("subprocess.run")
@patch("pygitgo.commands.repo.get_config", return_value="cached-token")
def test_get_github_token_cached(mock_get_config, mock_run):
    mock_run.side_effect = FileNotFoundError()
    assert _get_github_token() == "cached-token"
    mock_get_config.assert_called_once_with("github-token", "")


@patch.dict("os.environ", {}, clear=True)
@patch("subprocess.run")
@patch("pygitgo.commands.repo.get_config", return_value="")
@patch("pygitgo.commands.repo.open_url")
@patch("pygitgo.commands.repo.set_config")
@patch("builtins.input", return_value="user-pasted-token")
def test_get_github_token_prompt(mock_input, mock_set_config, mock_open_url, mock_get_config, mock_run):
    mock_run.side_effect = FileNotFoundError()
    assert _get_github_token() == "user-pasted-token"
    mock_open_url.assert_called_once()
    mock_set_config.assert_called_once_with("github-token", "user-pasted-token", silent=True)


@patch.dict("os.environ", {}, clear=True)
@patch("subprocess.run")
@patch("pygitgo.commands.repo.get_config", return_value="")
@patch("pygitgo.commands.repo.open_url")
@patch("builtins.input", return_value="")
def test_get_github_token_cancelled(mock_input, mock_open_url, mock_get_config, mock_run):
    mock_run.side_effect = FileNotFoundError()
    with pytest.raises(GitGoError, match="Cancelled"):
        _get_github_token()


@patch("urllib.request.urlopen")
def test_create_github_repo_success(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"clone_url": "https://github.com/user/repo.git"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    res = create_github_repo("repo", token="token")
    assert res["clone_url"] == "https://github.com/user/repo.git"


@patch("urllib.request.urlopen")
@patch("pygitgo.commands.repo._get_github_token", return_value="old-token")
@patch("pygitgo.commands.repo._prompt_for_token", return_value="new-token")
@patch("pygitgo.commands.repo._clear_saved_token")
def test_create_github_repo_401_retry(mock_clear, mock_prompt, mock_token, mock_urlopen):
    # First call fails with 401, second call (during retry) succeeds
    mock_error_resp = MagicMock()
    mock_error_resp.code = 401
    mock_error_resp.read.return_value = b'{"message": "Unauthorized"}'
    
    mock_success_resp = MagicMock()
    mock_success_resp.read.return_value = b'{"clone_url": "https://github.com/user/repo-retry.git"}'
    mock_success_resp.__enter__.return_value = mock_success_resp

    # We mock urlopen to raise HTTPError first, then return success response
    mock_urlopen.side_effect = [
        urllib.error.HTTPError("url", 401, "msg", {}, mock_error_resp),
        mock_success_resp
    ]

    res = create_github_repo("repo")
    assert res["clone_url"] == "https://github.com/user/repo-retry.git"
    mock_clear.assert_called_once()
    mock_prompt.assert_called_once()


@patch("pygitgo.commands.repo._get_github_token", return_value="token")
@patch("pygitgo.commands.repo.create_github_repo")
def test_repo_operation_verbose(mock_create, mock_token, capsys):
    mock_create.return_value = {"clone_url": "https://github.com/user/repo.git"}
    args = MagicMock()
    args.name = "repo"
    args.private = False
    args.description = "desc"

    url = repo_operation(args, silent=False)
    assert url == "https://github.com/user/repo.git"

    captured = capsys.readouterr()
    assert "Successfully created remote repository" in captured.out
    assert "gitgo link" in captured.out


@patch("pygitgo.commands.repo._get_github_token", return_value="token")
@patch("pygitgo.commands.repo.create_github_repo")
def test_repo_operation_silent(mock_create, mock_token, capsys):
    mock_create.return_value = {"clone_url": "https://github.com/user/repo.git"}
    args = MagicMock()
    args.name = "repo"
    args.private = False
    args.description = "desc"

    url = repo_operation(args, silent=True)
    assert url == "https://github.com/user/repo.git"

    captured = capsys.readouterr()
    assert "Successfully created remote repository" in captured.out
    assert "gitgo link" not in captured.out

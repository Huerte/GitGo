from unittest.mock import patch, MagicMock
from pygitgo.exceptions import GitGoError
from pygitgo.commands.repo import (
    _get_github_token,
    create_github_repo,
    repo_operation,
    _clear_saved_token,
    parse_repo_fullname,
    delete_github_repo
)
import urllib.error
import subprocess
import pytest
import sys

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
    mock_error_resp = MagicMock()
    mock_error_resp.code = 401
    mock_error_resp.read.return_value = b'{"message": "Unauthorized"}'
    
    mock_success_resp = MagicMock()
    mock_success_resp.read.return_value = b'{"clone_url": "https://github.com/user/repo-retry.git"}'
    mock_success_resp.__enter__.return_value = mock_success_resp

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

def test_clear_saved_token(mocker):
    mock_run = mocker.patch("subprocess.run")
    _clear_saved_token()
    mock_run.assert_called_once_with(
        ["git", "config", "--global", "--unset", "gitgo.github-token"],
        capture_output=True
    )

    mock_run.side_effect = Exception("failed")
    _clear_saved_token()

@patch.dict("os.environ", {}, clear=True)
def test_get_github_token_gh_cli_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["gh"], 5))
    mocker.patch("pygitgo.commands.repo.get_config", return_value="cached-token")
    assert _get_github_token() == "cached-token"

@patch("urllib.request.urlopen")
def test_create_github_repo_already_exists(mock_urlopen):
    mock_err = MagicMock()
    mock_err.code = 422
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 422, "Unprocessable Entity", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        create_github_repo("repo", token="token")
    assert "already exists on GitHub" in str(ex.value)

@patch("urllib.request.urlopen")
def test_create_github_repo_401_max_retries(mock_urlopen):
    mock_err = MagicMock()
    mock_err.code = 401
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 401, "Unauthorized", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        create_github_repo("repo", token="token", retry_count=3)
    assert "GitHub authentication failed" in str(ex.value)

@patch("urllib.request.urlopen")
def test_create_github_repo_other_http_errors(mock_urlopen):
    mock_err = MagicMock()
    mock_err.code = 500
    mock_err.read.return_value = b'{"message": "internal error"}'
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Internal Error", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        create_github_repo("repo", token="token")
    assert "GitHub API error 500: internal error" in str(ex.value)

    mock_err.read.return_value = b"plain text error"
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Internal Error", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        create_github_repo("repo", token="token")
    assert "GitHub API error 500: plain text error" in str(ex.value)

@patch("urllib.request.urlopen")
def test_create_github_repo_url_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("reason failure")
    with pytest.raises(GitGoError) as ex:
        create_github_repo("repo", token="token")
    assert "Network error creating repo: reason failure" in str(ex.value)

@patch("pygitgo.commands.repo._get_github_token", return_value="token")
@patch("pygitgo.commands.repo.create_github_repo")
def test_repo_operation_no_name(mock_create, mock_token, mocker):
    mock_create.return_value = {"clone_url": "https://github.com/user/current-dir.git"}
    mocker.patch("os.path.abspath", return_value="/path/current-dir")
    mocker.patch("os.path.basename", return_value="current-dir")
    args = MagicMock()
    args.name = None
    args.private = False
    args.description = None
    url = repo_operation(args, silent=True)
    assert url == "https://github.com/user/current-dir.git"

@patch("pygitgo.commands.repo._get_github_token", return_value="token")
@patch("pygitgo.commands.repo.create_github_repo")
def test_repo_operation_failure(mock_create, mock_token, mocker):
    mock_create.side_effect = Exception("failed creation")
    args = MagicMock()
    args.name = "repo"
    args.private = False
    args.description = None
    with pytest.raises(Exception):
         repo_operation(args, silent=True)

def test_parse_repo_fullname():
    assert parse_repo_fullname("https://github.com/owner/repo.git") == "owner/repo"
    assert parse_repo_fullname("git@github.com:owner/repo.git") == "owner/repo"
    assert parse_repo_fullname("invalid-url") is None

@patch("urllib.request.urlopen")
def test_delete_github_repo_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    assert delete_github_repo("owner/repo", token="token") is True

@patch("urllib.request.urlopen")
def test_delete_github_repo_403(mock_urlopen):
    mock_err = MagicMock()
    mock_err.code = 403
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 403, "Forbidden", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        delete_github_repo("owner/repo", token="token")
    assert "does not have 'delete_repo' scope" in str(ex.value)

@patch("urllib.request.urlopen")
def test_delete_github_repo_404(mock_urlopen):
    mock_err = MagicMock()
    mock_err.code = 404
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        delete_github_repo("owner/repo", token="token")
    assert "not found on GitHub" in str(ex.value)

@patch("urllib.request.urlopen")
def test_delete_github_repo_other_errors(mock_urlopen):
    mock_err = MagicMock()
    mock_err.code = 500
    mock_err.read.return_value = b'{"message": "delete error"}'
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Error", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        delete_github_repo("owner/repo", token="token")
    assert "GitHub API error 500 while deleting repo: delete error" in str(ex.value)

    mock_err.read.return_value = b"plain text error"
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Error", {}, mock_err)
    with pytest.raises(GitGoError) as ex:
        delete_github_repo("owner/repo", token="token")
    assert "GitHub API error 500 while deleting repo: plain text error" in str(ex.value)

@patch("urllib.request.urlopen")
def test_delete_github_repo_url_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("reason")
    with pytest.raises(GitGoError) as ex:
         delete_github_repo("owner/repo", token="token")
    assert "Network error deleting repo" in str(ex.value)

@patch("urllib.request.urlopen")
def test_delete_github_repo_generic_exception(mock_urlopen):
    mock_urlopen.side_effect = Exception("error")
    with pytest.raises(GitGoError) as ex:
         delete_github_repo("owner/repo", token="token")
    assert "Unexpected error" in str(ex.value)

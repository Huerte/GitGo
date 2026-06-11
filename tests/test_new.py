import pytest
from unittest.mock import patch, MagicMock
from pygitgo.commands.new import (
    _get_github_token,
    create_github_repo,
    new_operation,
)
from pygitgo.exceptions import GitGoError


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
@patch("pygitgo.commands.new.open_url")
@patch("builtins.input", return_value="user-pasted-token")
def test_get_github_token_guided(mock_input, mock_open_url, mock_run):
    mock_run.side_effect = FileNotFoundError()
    assert _get_github_token() == "user-pasted-token"
    mock_open_url.assert_called_once_with("https://github.com/settings/tokens/new?scopes=repo")


@patch.dict("os.environ", {}, clear=True)
@patch("subprocess.run")
@patch("pygitgo.commands.new.open_url")
@patch("builtins.input", return_value="")
def test_get_github_token_cancelled(mock_input, mock_open_url, mock_run):
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


@patch("pygitgo.commands.new._get_github_token", return_value="token")
@patch("pygitgo.commands.new.create_github_repo")
def test_new_operation(mock_create, mock_token, capsys):
    mock_create.return_value = {"clone_url": "https://github.com/user/repo.git"}
    args = MagicMock()
    args.name = "repo"
    args.private = False
    args.description = "desc"

    new_operation(args)

    captured = capsys.readouterr()
    assert "Successfully created remote repository" in captured.out
    assert "gitgo link" in captured.out
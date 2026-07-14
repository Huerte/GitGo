from pygitgo.commands.resolve import resolve_operation
from pygitgo.exceptions import GitCommandError, GitGoError
from unittest.mock import patch, MagicMock
from argparse import Namespace
import pytest

@patch("pygitgo.commands.resolve.abort_pull_conflict")
def test_resolve_abort_flag(mock_abort):
    args = Namespace(abort=True)
    resolve_operation(args)
    mock_abort.assert_called_once()

@patch("pygitgo.commands.resolve.Path")
def test_resolve_no_conflict(mock_path):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance
    
    args = Namespace(abort=False)
    with pytest.raises(GitGoError, match="No conflict resolution is currently in progress"):
        resolve_operation(args)

@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
@patch("pygitgo.commands.resolve.banner")
def test_resolve_success(mock_banner, mock_path, mock_run):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.side_effect = ["", "", ""]
    
    args = Namespace(abort=False)
    resolve_operation(args)
    
    assert mock_run.call_count == 3
    mock_run.assert_any_call(["git", "status", "--porcelain"])
    mock_run.assert_any_call(["git", "add", "."], loading_msg="Staging resolved files...", ok_text="Conflict fixes staged.")
    mock_run.assert_any_call(["git", "rebase", "--continue"], loading_msg="Finishing sync...", extra_env={"GIT_EDITOR": "true"})
    
    mock_banner.assert_called_once()

@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
def test_resolve_status_error(mock_path, mock_run):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.side_effect = GitCommandError(["git", "status"])
    
    args = Namespace(abort=False)
    with pytest.raises(GitGoError, match="Not inside a git repository"):
        resolve_operation(args)

@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
def test_resolve_still_conflicted(mock_path, mock_run):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.side_effect = [
        "",
        "",
        GitCommandError(["git", "rebase", "--continue"], stderr="you must edit all merge conflicts", returncode=1)
    ]
    
    args = Namespace(abort=False)
    with pytest.raises(GitGoError, match="You still have unresolved conflicts"):
        resolve_operation(args)

@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
def test_resolve_other_error(mock_path, mock_run):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.side_effect = [
        "",
        "",
        GitCommandError(["git", "rebase", "--continue"], stderr="some weird error occurred", returncode=1)
    ]
    
    args = Namespace(abort=False)
    with pytest.raises(GitGoError, match="Resolve failed: some weird error occurred"):
        resolve_operation(args)

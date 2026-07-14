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

@patch("pygitgo.commands.resolve.subprocess.run")
@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
@patch("pygitgo.commands.resolve.banner")
@patch("pygitgo.commands.resolve.yaspin")
def test_resolve_success(mock_yaspin, mock_banner, mock_path, mock_run, mock_subrun):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.side_effect = ["", ""]
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_subrun.return_value = mock_result
    
    args = Namespace(abort=False)
    resolve_operation(args)
    
    assert mock_run.call_count == 2
    mock_run.assert_any_call(["git", "status", "--porcelain"])
    mock_run.assert_any_call(["git", "add", "."], loading_msg="Staging resolved files...", ok_text="Conflict fixes staged.")
    
    mock_subrun.assert_called_once()
    called_args = mock_subrun.call_args
    assert called_args[0][0] == ["git", "rebase", "--continue"]
    assert "GIT_EDITOR" in called_args[1]["env"]
    assert called_args[1]["env"]["GIT_EDITOR"] == "true"
    
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

@patch("pygitgo.commands.resolve.subprocess.run")
@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
@patch("pygitgo.commands.resolve.yaspin")
def test_resolve_still_conflicted(mock_yaspin, mock_path, mock_run, mock_subrun):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.return_value = ""
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "you must edit all merge conflicts"
    mock_subrun.return_value = mock_result
    
    args = Namespace(abort=False)
    with pytest.raises(GitGoError, match="You still have unresolved conflicts"):
        resolve_operation(args)

@patch("pygitgo.commands.resolve.subprocess.run")
@patch("pygitgo.commands.resolve.run_command")
@patch("pygitgo.commands.resolve.Path")
@patch("pygitgo.commands.resolve.yaspin")
def test_resolve_other_error(mock_yaspin, mock_path, mock_run, mock_subrun):
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance
    
    mock_run.return_value = ""
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "some weird error occurred"
    mock_subrun.return_value = mock_result
    
    args = Namespace(abort=False)
    with pytest.raises(GitGoError, match="Resolve failed: some weird error occurred"):
        resolve_operation(args)

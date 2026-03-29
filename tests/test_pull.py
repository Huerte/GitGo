import pytest
from unittest.mock import patch, MagicMock
from pygitgo.commands.pull import pull_operation
from pygitgo.exceptions import GitCommandError
from argparse import Namespace
import subprocess

@patch("pygitgo.commands.pull.run_command")
@patch("pygitgo.commands.pull.success")
@patch("pygitgo.commands.pull.get_current_branch", return_value="main")
def test_pull_operation_success_no_branch(mock_get_branch, mock_success, mock_run_command):
    mock_run_command.side_effect = [
        "1234567890abcdef",  
        None                 
    ]
    
    args = Namespace(branch=None)
    pull_operation(args)
    
    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(["git", "ls-remote", "--heads", "origin", "main"], allow_fail=True)
    mock_run_command.assert_any_call(
        ["git", "pull", "--rebase", "--autostash", "origin", "main"], 
        loading_msg="Downloading latest updates for 'main' (auto-saving your code)..."
    )
    mock_success.assert_called_once()

@patch("pygitgo.commands.pull.run_command")
@patch("pygitgo.commands.pull.success")
def test_pull_operation_success_with_branch(mock_success, mock_run_command):
    mock_run_command.side_effect = [
        "1234567890abcdef",  
        None                 
    ]
    
    args = Namespace(branch="feature/test")
    pull_operation(args)
    
    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(["git", "ls-remote", "--heads", "origin", "feature/test"], allow_fail=True)
    mock_run_command.assert_any_call(
        ["git", "pull", "--rebase", "--autostash", "origin", "feature/test"], 
        loading_msg="Downloading latest updates for 'feature/test' (auto-saving your code)..."
    )
    mock_success.assert_called_once()

@patch("pygitgo.commands.pull.sys.exit")
@patch("pygitgo.commands.pull.error")
@patch("pygitgo.commands.pull.run_command")
def test_pull_operation_branch_not_found(mock_run_command, mock_error, mock_exit):
    mock_run_command.return_value = subprocess.CalledProcessError(128, ["git", "ls-remote"])
    
    args = Namespace(branch="does-not-exist")
    pull_operation(args)
    
    mock_exit.assert_called_once_with(1)
    mock_error.assert_called()

@patch("pygitgo.commands.pull.sys.exit")
@patch("pygitgo.commands.pull.error")
@patch("pygitgo.commands.pull.run_command")
def test_pull_operation_merge_conflict(mock_run_command, mock_error, mock_exit):
    conflict_err = GitCommandError(["git", "pull"], stderr="merge conflict in file.py")

    def side_effect_fn(*args, **kwargs):
        cmd = args[0]
        if cmd[1] == "ls-remote":
            return "1234567890abcdef"
        raise conflict_err

    mock_run_command.side_effect = side_effect_fn
    
    args = Namespace(branch="main")
    pull_operation(args)
    
    mock_exit.assert_called_once_with(1)
    mock_error.assert_any_call("\nMERGE CONFLICT DETECTED!")

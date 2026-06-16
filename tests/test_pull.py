from unittest.mock import patch, MagicMock
from pygitgo.commands.pull import pull_operation
from pygitgo.exceptions import GitCommandError, GitGoError
from argparse import Namespace
import subprocess
import pytest

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
    mock_run_command.assert_any_call(
        ["git", "ls-remote", "--heads", "origin", "main"],
        loading_msg="Checking if 'main' exists on remote...",
        ok_text="Branch 'main' found on remote.",
        err_text="Branch 'main' does not exist on the remote."
    )
    mock_run_command.assert_any_call(
        ["git", "pull", "--rebase", "--autostash", "origin", "main"], 
        loading_msg="Downloading latest updates for 'main' (auto-saving your code)...",
        ok_text="Project is up to date with 'main'."
    )
    mock_success.assert_not_called()

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
    mock_run_command.assert_any_call(
        ["git", "ls-remote", "--heads", "origin", "feature/test"],
        loading_msg="Checking if 'feature/test' exists on remote...",
        ok_text="Branch 'feature/test' found on remote.",
        err_text="Branch 'feature/test' does not exist on the remote."
    )
    mock_run_command.assert_any_call(
        ["git", "pull", "--rebase", "--autostash", "origin", "feature/test"], 
        loading_msg="Downloading latest updates for 'feature/test' (auto-saving your code)...",
        ok_text="Project is up to date with 'feature/test'."
    )
    mock_success.assert_not_called()

@patch("pygitgo.commands.pull.run_command")
def test_pull_operation_branch_not_found(mock_run_command):
    mock_run_command.side_effect = GitCommandError(["git", "ls-remote"])
    
    args = Namespace(branch="does-not-exist")
    with pytest.raises(GitGoError):
        pull_operation(args)

@patch("pygitgo.commands.pull.run_command")
def test_pull_operation_merge_conflict(mock_run_command):
    conflict_err = GitCommandError(["git", "pull"], stderr="merge conflict in file.py")

    def side_effect_fn(*args, **kwargs):
        cmd = args[0]
        if cmd[1] == "ls-remote":
            return "1234567890abcdef"
        raise conflict_err

    mock_run_command.side_effect = side_effect_fn
    
    args = Namespace(branch="main")
    with pytest.raises(GitGoError):
        pull_operation(args)


@patch("pygitgo.commands.pull.run_command")
@patch("pygitgo.commands.pull.success")
@patch("pygitgo.commands.pull.warning")
@patch("pygitgo.commands.pull.Path")
def test_pull_keyboard_interrupt_rebase_in_progress(mock_path, mock_warning, mock_success, mock_run_command):
    def side_effect_fn(*args, **kwargs):
        cmd = args[0]
        if cmd[1] == "ls-remote":
            return "1234567890abcdef"
        if cmd[1] == "pull":
            raise KeyboardInterrupt()
        return ""

    mock_run_command.side_effect = side_effect_fn

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path.return_value = mock_path_instance

    args = Namespace(branch="main")
    with pytest.raises(SystemExit) as sys_exit:
        pull_operation(args)

    assert sys_exit.value.code == 130
    mock_run_command.assert_any_call(["git", "rebase", "--abort"], loading_msg="Aborting interrupted rebase...", ok_text="Rebase aborted. Branch is back to its pre-pull state.")
    mock_warning.assert_any_call("Pull interrupted (Ctrl+C).")
    mock_warning.assert_any_call("A rebase is in progress from the interrupted pull.")
    mock_success.assert_not_called()


@patch("pygitgo.commands.pull.run_command")
@patch("pygitgo.commands.pull.success")
@patch("pygitgo.commands.pull.warning")
@patch("pygitgo.commands.pull.Path")
def test_pull_keyboard_interrupt_no_rebase(mock_path, mock_warning, mock_success, mock_run_command):
    def side_effect_fn(*args, **kwargs):
        cmd = args[0]
        if cmd[1] == "ls-remote":
            return "1234567890abcdef"
        if cmd[1] == "pull":
            raise KeyboardInterrupt()
        return ""

    mock_run_command.side_effect = side_effect_fn

    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = False
    mock_path.return_value = mock_path_instance

    args = Namespace(branch="main")
    with pytest.raises(SystemExit) as sys_exit:
        pull_operation(args)

    assert sys_exit.value.code == 130
    for call in mock_run_command.call_args_list:
        assert "--abort" not in call[0][0]
    mock_success.assert_called_with("No partial rebase detected. Branch is clean.")

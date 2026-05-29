import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
from pygitgo.commands.clean import clean_operation
from pygitgo.exceptions import GitGoError

@patch("pygitgo.commands.clean.get_main_branch", return_value="main")
@patch("pygitgo.commands.clean.get_current_branch", return_value="main")
@patch("pygitgo.commands.clean.run_command")
def test_clean_no_branches(mock_run, mock_current, mock_main, mocker):
    mock_run.side_effect = ["main\n", "main\n"]  # local branches, merged branches
    fake_info = mocker.patch("pygitgo.commands.clean.info")
    
    args = Namespace(all=False, keep=None, yes=True)
    clean_operation(args)
    
    fake_info.assert_called_with("\nNo branches to delete. Your workspace is already clean.\n")

@patch("pygitgo.commands.clean.get_main_branch", return_value="main")
@patch("pygitgo.commands.clean.get_current_branch", return_value="main")
@patch("pygitgo.commands.clean.run_command")
@patch("pygitgo.commands.clean.input", return_value="y")
def test_clean_merged_branches(mock_input, mock_run, mock_current, mock_main, mocker):
    # Mock branch lists
    mock_run.side_effect = [
        "main\nfeature/1\ndev\n",  # local branches
        "main\nfeature/1\n",       # merged branches
        ""                         # result of delete command
    ]
    fake_success = mocker.patch("pygitgo.commands.clean.success")
    
    args = Namespace(all=False, keep=None, yes=False)
    clean_operation(args)
    
    # Should delete feature/1 but keep dev because dev is not merged
    mock_run.assert_any_call(["git", "branch", "-d", "feature/1"])
    fake_success.assert_any_call("Deleted branch: feature/1")

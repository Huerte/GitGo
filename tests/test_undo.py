import pytest
from unittest.mock import patch, MagicMock
from pygitgo.commands.undo import undo_commit, undo_add, undo_changes, undo_operations
from pygitgo.exceptions import GitCommandError
from argparse import Namespace

@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_commit_success(mock_success, mock_run_command):
    undo_commit()
    mock_run_command.assert_called_once_with(["git", "reset", "--soft", "HEAD~"])
    mock_success.assert_called_once()


@patch("pygitgo.commands.undo.sys.exit")
@patch("pygitgo.commands.undo.error")
@patch("pygitgo.commands.undo.run_command")
def test_undo_commit_failure(mock_run_command, mock_error, mock_exit):
    mock_run_command.side_effect = GitCommandError(["git", "reset", "--soft", "HEAD~"])
    undo_commit()
    mock_run_command.assert_called_once()
    assert mock_error.call_count == 2
    mock_exit.assert_called_once_with(1)


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_add_success(mock_success, mock_run_command):
    undo_add()
    mock_run_command.assert_called_once_with(["git", "reset", "HEAD"])
    mock_success.assert_called_once()


@patch("pygitgo.commands.undo.sys.exit")
@patch("pygitgo.commands.undo.error")
@patch("pygitgo.commands.undo.run_command")
def test_undo_add_failure(mock_run_command, mock_error, mock_exit):
    mock_run_command.side_effect = GitCommandError(["git", "reset", "HEAD"])
    undo_add()
    mock_run_command.assert_called_once()
    mock_error.assert_called_once()
    mock_exit.assert_called_once_with(1)


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
@patch("pygitgo.commands.undo.input", return_value="y")
def test_undo_changes_success(mock_input, mock_success, mock_run_command):
    undo_changes()
    mock_input.assert_called_once()
    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...")
    mock_run_command.assert_any_call(["git", "clean", "-fd"], loading_msg="Removing new files...")
    mock_success.assert_called_once()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.info")
@patch("pygitgo.commands.undo.input", return_value="n")
def test_undo_changes_abort(mock_input, mock_info, mock_run_command):
    undo_changes()
    mock_input.assert_called_once()
    mock_info.assert_called_once()
    mock_run_command.assert_not_called()


@patch("pygitgo.commands.undo.undo_commit")
def test_undo_operations_commit(mock_undo_commit):
    args = Namespace(action="commit")
    undo_operations(args)
    mock_undo_commit.assert_called_once()


@patch("pygitgo.commands.undo.undo_add")
def test_undo_operations_add(mock_undo_add):
    args = Namespace(action="add")
    undo_operations(args)
    mock_undo_add.assert_called_once()


@patch("pygitgo.commands.undo.undo_changes")
def test_undo_operations_changes(mock_undo_changes):
    args = Namespace(action="changes")
    undo_operations(args)
    mock_undo_changes.assert_called_once()


@patch("pygitgo.commands.undo.sys.exit")
@patch("pygitgo.commands.undo.error")
def test_undo_operations_invalid(mock_error, mock_exit):
    args = Namespace(action="invalid")
    undo_operations(args)
    mock_error.assert_called_once()
    mock_exit.assert_called_once_with(1)

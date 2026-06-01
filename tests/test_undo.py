import pytest
from unittest.mock import patch, MagicMock
from pygitgo.commands.undo import undo_commit, undo_add, undo_changes, undo_operation
from pygitgo.exceptions import GitGoError, GitCommandError
from argparse import Namespace

@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_commit_success(mock_success, mock_run_command):
    undo_commit()
    mock_run_command.assert_called_once_with(["git", "reset", "--soft", "HEAD~"])
    mock_success.assert_called_once()


@patch("pygitgo.commands.undo.run_command")
def test_undo_commit_failure(mock_run_command):
    mock_run_command.side_effect = GitCommandError(["git", "reset", "--soft", "HEAD~"])
    with pytest.raises(GitGoError):
        undo_commit()
    mock_run_command.assert_called_once()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_add_success(mock_success, mock_run_command):
    undo_add()
    mock_run_command.assert_called_once_with(["git", "reset", "HEAD"])
    mock_success.assert_called_once()


@patch("pygitgo.commands.undo.run_command")
def test_undo_add_failure(mock_run_command):
    mock_run_command.side_effect = GitCommandError(["git", "reset", "HEAD"])
    with pytest.raises(GitCommandError):
        undo_add()
    mock_run_command.assert_called_once()


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
def test_undo_operation_commit(mock_undo_commit):
    args = Namespace(action="commit")
    undo_operation(args)
    mock_undo_commit.assert_called_once()


@patch("pygitgo.commands.undo.undo_add")
def test_undo_operation_add(mock_undo_add):
    args = Namespace(action="add")
    undo_operation(args)
    mock_undo_add.assert_called_once()


@patch("pygitgo.commands.undo.undo_changes")
def test_undo_operation_changes(mock_undo_changes):
    args = Namespace(action="changes")
    undo_operation(args)
    mock_undo_changes.assert_called_once()


def test_undo_operation_invalid():
    args = Namespace(action="invalid")
    with pytest.raises(GitGoError):
        undo_operation(args)

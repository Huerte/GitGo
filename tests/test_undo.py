import pytest
from unittest.mock import patch, MagicMock, call
from pygitgo.commands.undo import undo_commit, undo_add, undo_changes, undo_link, undo_push, undo_operation
from pygitgo.exceptions import GitGoError, GitCommandError
from argparse import Namespace


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_commit_success(mock_success, mock_run_command):
    undo_commit()
    mock_run_command.assert_called_once_with(
        ["git", "reset", "--soft", "HEAD~"],
        loading_msg="Undoing last commit...",
        ok_text="Last commit undone. Files are untouched."
    )
    mock_success.assert_not_called()


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
    mock_run_command.assert_called_once_with(
        ["git", "reset", "HEAD"],
        loading_msg="Clearing staging area...",
        ok_text="Staging cleared. Files are back to unstaged."
    )
    mock_success.assert_not_called()


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
    mock_run_command.assert_any_call(["git", "clean", "-fd"], loading_msg="Removing new files...", ok_text="Working tree reset. All changes discarded.")
    mock_success.assert_not_called()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.info")
@patch("pygitgo.commands.undo.input", return_value="n")
def test_undo_changes_abort(mock_input, mock_info, mock_run_command):
    undo_changes()
    mock_input.assert_called_once()
    mock_info.assert_called_once()
    mock_run_command.assert_not_called()



@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_link_success(mock_success, mock_run_command):
    undo_link()
    mock_run_command.assert_any_call(
        ["git", "remote", "remove", "origin"],
        loading_msg="Removing remote 'origin'...",
        ok_text="Remote 'origin' removed."
    )
    mock_run_command.assert_any_call(
        ["git", "reset", "--soft", "HEAD~"],
        loading_msg="Undoing initial commit...",
        ok_text="Initial commit undone. Files are back to staged, ready to re-link."
    )
    mock_success.assert_not_called()


@patch("pygitgo.commands.undo.run_command")
def test_undo_link_no_remote(mock_run_command):
    mock_run_command.side_effect = GitCommandError(["git", "remote", "remove", "origin"])
    with pytest.raises(GitGoError, match="Could not remove remote"):
        undo_link()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
@patch("pygitgo.commands.undo.info")
def test_undo_link_no_commit_to_reset(mock_info, mock_success, mock_run_command):
    mock_run_command.side_effect = [None, GitCommandError(["git", "reset"])]
    undo_link()
    mock_run_command.assert_any_call(
        ["git", "remote", "remove", "origin"],
        loading_msg="Removing remote 'origin'...",
        ok_text="Remote 'origin' removed."
    )
    mock_success.assert_not_called()
    assert mock_info.call_count == 2



@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.success")
@patch("pygitgo.commands.undo.input", return_value="y")
def test_undo_push_success(mock_input, mock_success, mock_branch, mock_run_command):
    undo_push()
    mock_run_command.assert_any_call(["git", "reset", "--soft", "HEAD~"], loading_msg="Reverting last commit locally...")
    mock_run_command.assert_any_call(["git", "push", "--force", "origin", "main"], loading_msg="Force-pushing reverted state to 'main'...", ok_text="Last push reverted. Remote 'main' is back to the previous commit.")
    mock_success.assert_not_called()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.info")
@patch("pygitgo.commands.undo.input", return_value="n")
def test_undo_push_abort(mock_input, mock_info, mock_branch, mock_run_command):
    undo_push()
    mock_run_command.assert_not_called()
    mock_info.assert_called_once_with("Canceled. Remote is unchanged.")


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.input", return_value="y")
def test_undo_push_no_commit(mock_input, mock_branch, mock_run_command):
    mock_run_command.side_effect = GitCommandError(["git", "reset"])
    with pytest.raises(GitGoError, match="Undo failed"):
        undo_push()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.input", return_value="y")
def test_undo_push_force_push_fails(mock_input, mock_branch, mock_run_command):
    mock_run_command.side_effect = [None, GitCommandError(["git", "push", "--force"])]
    with pytest.raises(GitGoError, match="Force-push failed"):
        undo_push()


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


@patch("pygitgo.commands.undo.undo_link")
def test_undo_operation_link(mock_undo_link):
    args = Namespace(action="link")
    undo_operation(args)
    mock_undo_link.assert_called_once()


@patch("pygitgo.commands.undo.undo_push")
def test_undo_operation_push(mock_undo_push):
    args = Namespace(action="push")
    undo_operation(args)
    mock_undo_push.assert_called_once()


def test_undo_operation_invalid():
    args = Namespace(action="invalid")
    with pytest.raises(GitGoError):
        undo_operation(args)

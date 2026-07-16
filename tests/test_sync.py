from unittest.mock import patch
from argparse import Namespace
import pytest

from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.sync import sync_operation

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
def test_sync_not_git_repo(mock_ensure_inside_git):
    mock_ensure_inside_git.side_effect = GitGoError("Not inside a git repository. Run 'gitgo init' or 'gitgo link' first.")
    args = Namespace(message="hello")
    with pytest.raises(GitGoError, match="Not inside a git repository"):
        sync_operation(args)

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch")
def test_sync_current_branch_error(mock_get_branch, mock_ensure_inside_git):
    mock_get_branch.side_effect = GitCommandError(["git", "branch"], stderr="fatal: not a git repository")
    args = Namespace(message="hello")
    with pytest.raises(GitGoError, match="Could not determine current branch"):
        sync_operation(args)

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync.git_commit", return_value=True)
@patch("pygitgo.commands.sync.git_push")
@patch("pygitgo.commands.sync.banner")
def test_sync_remote_not_exists(mock_banner, mock_push, mock_commit, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    # ls-remote fails -> remote_exists = False
    mock_run_command.side_effect = GitCommandError(["git", "ls-remote"])
    
    args = Namespace(message="test msg")
    sync_operation(args)

    # Should not call pull
    for call in mock_run_command.call_args_list:
        assert "pull" not in call[0][0]

    mock_commit.assert_called_with("test msg")
    mock_push.assert_called_with("main")
    mock_banner.assert_called_once()

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync.git_commit", return_value=True)
@patch("pygitgo.commands.sync.git_push")
@patch("pygitgo.commands.sync.banner")
def test_sync_happy_path_with_message(mock_banner, mock_push, mock_commit, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    # ls-remote succeeds, pull succeeds
    mock_run_command.side_effect = ["", ""]

    args = Namespace(message="test msg")
    sync_operation(args)

    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(["git", "ls-remote", "--exit-code", "--heads", "origin", "main"])
    mock_run_command.assert_any_call(
        ["git", "pull", "--rebase", "--autostash", "origin", "main"],
        loading_msg="Downloading latest updates for 'main'...",
        ok_text="Successfully pulled latest changes."
    )
    mock_commit.assert_called_with("test msg")
    mock_push.assert_called_with("main")
    mock_banner.assert_called_once()

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync.git_commit", return_value=True)
@patch("pygitgo.commands.sync.git_push")
@patch("pygitgo.commands.sync.get_config", return_value="default msg")
def test_sync_happy_path_no_message(mock_get_config, mock_push, mock_commit, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    mock_run_command.side_effect = ["", ""]

    args = Namespace(message=None)
    sync_operation(args)

    mock_get_config.assert_called_with("default-message", "chore: new changes applied")
    mock_commit.assert_called_with("default msg")

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync._pull_interrupt_cleanup")
def test_sync_keyboard_interrupt(mock_cleanup, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    def side_effect(*args, **kwargs):
        if args[0][1] == "pull":
            raise KeyboardInterrupt()
        return ""
    mock_run_command.side_effect = side_effect

    args = Namespace(message="msg")
    with pytest.raises(SystemExit) as sys_exit:
        sync_operation(args)

    assert sys_exit.value.code == 130
    mock_cleanup.assert_called_once()

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
def test_sync_merge_conflict(mock_run_command, mock_get_branch, mock_ensure_inside_git):
    def side_effect(*args, **kwargs):
        if args[0][1] == "pull":
            raise GitCommandError(["git", "pull"], stderr="merge conflict detected")
        return ""
    mock_run_command.side_effect = side_effect

    args = Namespace(message="msg")
    with pytest.raises(GitGoError, match="Sync paused — resolve conflicts to continue"):
        sync_operation(args)

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync.git_commit", return_value=False)
@patch("pygitgo.commands.sync.git_push")
@patch("pygitgo.commands.sync.banner")
def test_sync_no_new_changes_but_unpushed(mock_banner, mock_push, mock_commit, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    def side_effect(*args, **kwargs):
        if args[0][1] == "log":
            return "abcdef1 unpushed commit"
        return ""
    mock_run_command.side_effect = side_effect

    args = Namespace(message="msg")
    sync_operation(args)

    mock_push.assert_called_with("main")
    mock_banner.assert_called_once()

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync.git_commit", return_value=False)
@patch("pygitgo.commands.sync.git_push")
def test_sync_clean_tree(mock_push, mock_commit, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    def side_effect(*args, **kwargs):
        if args[0][1] == "log":
            return "   "  # Empty output meaning no unpushed commits
        return ""
    mock_run_command.side_effect = side_effect

    args = Namespace(message="msg")
    sync_operation(args)

    # Should exit early, so push is never called
    mock_push.assert_not_called()

@patch("pygitgo.commands.sync.ensure_inside_git_repository")
@patch("pygitgo.commands.sync.get_current_branch", return_value="main")
@patch("pygitgo.commands.sync.run_command")
@patch("pygitgo.commands.sync.git_commit", return_value=False)
@patch("pygitgo.commands.sync.git_push")
@patch("pygitgo.commands.sync.banner")
def test_sync_unpushed_check_fails(mock_banner, mock_push, mock_commit, mock_run_command, mock_get_branch, mock_ensure_inside_git):
    def side_effect(*args, **kwargs):
        if args[0][1] == "log":
            raise GitCommandError(["git", "log"], stderr="fatal: bad revision")
        return ""
    mock_run_command.side_effect = side_effect

    args = Namespace(message="msg")
    sync_operation(args)

    # Falls back to push
    mock_push.assert_called_with("main")
    mock_banner.assert_called_once()

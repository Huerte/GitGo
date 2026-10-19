from pygitgo.commands.undo import undo_commit, undo_add, undo_changes, undo_link, undo_push, undo_operation
from pygitgo.exceptions import GitGoError, GitCommandError
from unittest.mock import patch
from argparse import Namespace
import pytest


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
@patch("pygitgo.commands.undo.success")
def test_undo_commit_initial_fallback(mock_success, mock_run_command):
    mock_run_command.side_effect = [GitCommandError(["git", "reset"]), None]
    undo_commit()
    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(["git", "update-ref", "-d", "HEAD"], loading_msg="Undoing initial commit...", ok_text="Initial commit undone. Files are back to staged.")

@patch("pygitgo.commands.undo.run_command")
def test_undo_commit_total_failure(mock_run_command):
    mock_run_command.side_effect = [GitCommandError(["git", "reset"]), GitCommandError(["git", "update-ref"])]
    with pytest.raises(GitGoError):
        undo_commit()
    assert mock_run_command.call_count == 2


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.success")
def test_undo_add_success(mock_success, mock_run_command):
    mock_run_command.side_effect = ["file.txt", None]
    undo_add()
    assert mock_run_command.call_count == 2
    mock_run_command.assert_any_call(
        ["git", "reset", "HEAD"],
        loading_msg="Clearing staging area...",
        ok_text="Staging cleared. Files are back to unstaged."
    )
    mock_success.assert_not_called()


@patch("pygitgo.commands.undo.run_command")
def test_undo_add_failure(mock_run_command):
    mock_run_command.side_effect = ["file.txt", GitCommandError(["git", "reset", "HEAD"])]
    with pytest.raises(GitCommandError):
        undo_add()
    assert mock_run_command.call_count == 2


CHANGED = [{"status": "M", "label": "modified", "path": "a.py"}, {"status": "??", "label": "new file", "path": "b.txt"}]


@patch("pygitgo.commands.staging.get_changed_files", return_value=CHANGED)
@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.confirm", return_value=True)
def test_undo_changes_saves_backup_by_default(mock_confirm, mock_run_command, mock_files):
    assert undo_changes() is True
    cmd = mock_run_command.call_args.args[0]
    assert cmd[:5] == ["git", "stash", "push", "--include-untracked", "-m"]
    assert "GitGo undo-changes backup" in cmd[5]
    assert not any("--hard" in c.args[0] for c in mock_run_command.call_args_list)


@patch("pygitgo.commands.staging.get_changed_files", return_value=CHANGED)
@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.confirm", return_value=True)
def test_undo_changes_permanent_skips_backup(mock_confirm, mock_run_command, mock_files):
    undo_changes(permanent=True)
    mock_run_command.assert_any_call(["git", "reset", "--hard", "HEAD"], loading_msg="Throwing away edits...", ok_text="Edits discarded.")
    mock_run_command.assert_any_call(["git", "clean", "-fd"], loading_msg="Removing new files...", ok_text="Working tree reset. All changes discarded.")
    assert mock_confirm.call_args.kwargs.get("destructive") is True


@patch("pygitgo.commands.staging.get_changed_files", return_value=CHANGED)
@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.confirm", return_value=False)
def test_undo_changes_abort(mock_confirm, mock_run_command, mock_files):
    assert undo_changes() is False
    mock_run_command.assert_not_called()


@patch("pygitgo.commands.staging.get_changed_files", return_value=[])
@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.confirm")
def test_undo_changes_clean_tree_does_nothing(mock_confirm, mock_run_command, mock_files):
    assert undo_changes() is False
    mock_confirm.assert_not_called()
    mock_run_command.assert_not_called()


@patch("pygitgo.commands.staging.get_changed_files", return_value=CHANGED)
@patch("pygitgo.commands.undo.run_command", side_effect=GitCommandError(["git", "stash"]))
@patch("pygitgo.commands.undo.confirm", return_value=True)
def test_undo_changes_backup_failure_discards_nothing(mock_confirm, mock_run_command, mock_files):
    with pytest.raises(GitGoError, match="nothing was discarded"):
        undo_changes()


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


def _push_run(unpushed="0", behind="0", extra=None):
    """Fake run_command for undo_push: answers the safety checks, then succeeds."""
    def _run(cmd, *args, **kwargs):
        if cmd[:3] == ["git", "rev-list", "--count"]:
            return unpushed if cmd[3].endswith("..HEAD") else behind
        if cmd[:2] == ["git", "log"]:
            return "abc1234 add feature"
        if extra:
            return extra(cmd)
        return ""
    return _run


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.confirm", return_value=True)
def test_undo_push_success(mock_confirm, mock_branch, mock_run_command):
    mock_run_command.side_effect = _push_run()
    assert undo_push() is True
    mock_run_command.assert_any_call(["git", "reset", "--soft", "HEAD~"], loading_msg="Reverting last commit locally...", ok_text="Last commit reverted locally.")
    mock_run_command.assert_any_call(["git", "push", "--force-with-lease", "origin", "main"], loading_msg="Force-pushing reverted state to 'main'...", ok_text="Last push reverted. Remote 'main' is back to the previous commit.")


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.info")
@patch("pygitgo.commands.undo.confirm", return_value=False)
def test_undo_push_abort(mock_confirm, mock_info, mock_branch, mock_run_command):
    mock_run_command.side_effect = _push_run()
    assert undo_push() is False
    assert not any(c.args[0][:2] == ["git", "reset"] for c in mock_run_command.call_args_list)
    mock_info.assert_called_once_with("Canceled. Remote is unchanged.")


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.confirm")
def test_undo_push_refuses_with_unpushed_local_commits(mock_confirm, mock_branch, mock_run_command):
    mock_run_command.side_effect = _push_run(unpushed="2")
    with pytest.raises(GitGoError, match="never pushed"):
        undo_push()
    mock_confirm.assert_not_called()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.confirm")
def test_undo_push_refuses_when_remote_is_ahead(mock_confirm, mock_branch, mock_run_command):
    mock_run_command.side_effect = _push_run(behind="1")
    with pytest.raises(GitGoError, match="newer commit"):
        undo_push()
    mock_confirm.assert_not_called()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
def test_undo_push_refuses_when_branch_never_pushed(mock_branch, mock_run_command):
    mock_run_command.side_effect = GitCommandError(["git", "rev-list"])
    with pytest.raises(GitGoError, match="Has this branch been pushed"):
        undo_push()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.confirm", return_value=True)
def test_undo_push_no_commit(mock_confirm, mock_branch, mock_run_command):
    def boom(cmd):
        if cmd[:2] == ["git", "reset"]:
            raise GitCommandError(cmd)
        return ""
    mock_run_command.side_effect = _push_run(extra=boom)
    with pytest.raises(GitGoError, match="Undo failed"):
        undo_push()


@patch("pygitgo.commands.undo.run_command")
@patch("pygitgo.commands.undo.get_current_branch", return_value="main")
@patch("pygitgo.commands.undo.confirm", return_value=True)
def test_undo_push_force_push_fails(mock_confirm, mock_branch, mock_run_command):
    def boom(cmd):
        if cmd[:2] == ["git", "push"]:
            raise GitCommandError(cmd)
        return ""
    mock_run_command.side_effect = _push_run(extra=boom)
    with pytest.raises(GitGoError, match="Force-push failed"):
        undo_push()


@patch("pygitgo.commands.undo.undo_commit", return_value=True)
@patch("pygitgo.commands.undo.banner")
def test_undo_operation_commit(mock_banner, mock_undo_commit):
    args = Namespace(action="commit")
    undo_operation(args)
    mock_undo_commit.assert_called_once()
    mock_banner.assert_called_once()


@patch("pygitgo.commands.undo.undo_add", return_value=True)
@patch("pygitgo.commands.undo.banner")
def test_undo_operation_add(mock_banner, mock_undo_add):
    args = Namespace(action="add")
    undo_operation(args)
    mock_undo_add.assert_called_once()
    mock_banner.assert_called_once()


@patch("pygitgo.commands.undo.undo_changes", return_value=False)
@patch("pygitgo.commands.undo.banner")
def test_undo_operation_changes(mock_banner, mock_undo_changes):
    args = Namespace(action="changes")
    undo_operation(args)
    mock_undo_changes.assert_called_once()
    # banner should NOT fire when user aborts (returns False)
    mock_banner.assert_not_called()


@patch("pygitgo.commands.undo.undo_link", return_value=True)
@patch("pygitgo.commands.undo.banner")
def test_undo_operation_link(mock_banner, mock_undo_link):
    args = Namespace(action="link")
    undo_operation(args)
    mock_undo_link.assert_called_once()
    mock_banner.assert_called_once()


@patch("pygitgo.commands.undo.undo_push", return_value=False)
@patch("pygitgo.commands.undo.banner")
def test_undo_operation_push(mock_banner, mock_undo_push):
    args = Namespace(action="push")
    undo_operation(args)
    mock_undo_push.assert_called_once()
    # banner should NOT fire when user aborts (returns False)
    mock_banner.assert_not_called()


def test_undo_operation_invalid():
    args = Namespace(action="invalid")
    with pytest.raises(GitGoError):
        undo_operation(args)

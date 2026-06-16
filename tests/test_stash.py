import pytest
from pygitgo.exceptions import GitCommandError
from pygitgo.commands.stash import (
    git_stash_push, git_stash_pop, git_stash_apply,
    git_stash_drop, git_stash_list, git_stash_clear
)


def test_git_stash_push_success(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Saved working directory and index state WIP on main")
    result = git_stash_push()
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "push", "-u", "-m", "GitGo Auto-Stash"],
        loading_msg="Saving your changes...",
        ok_text="Changes saved."
    )


def test_git_stash_push_no_changes(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="No local changes to save")
    result = git_stash_push()
    assert result is False


def test_git_stash_push_failure(mocker):
    fake_run = mocker.patch(
        "pygitgo.commands.stash.run_command",
        side_effect=GitCommandError(["git", "stash", "push"])
    )
    result = git_stash_push()
    assert result is False


def test_git_stash_pop_success(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Dropped refs/stash@{0}")
    result = git_stash_pop()
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "pop"],
        loading_msg="Restoring your saved changes...",
        ok_text="Changes restored."
    )


def test_git_stash_pop_failure(mocker):
    fake_run = mocker.patch(
        "pygitgo.commands.stash.run_command",
        side_effect=GitCommandError(["git", "stash", "pop"])
    )
    result = git_stash_pop()
    assert result is False


def test_git_stash_apply_success_no_id(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Applied stash")
    result = git_stash_apply()
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "apply"],
        loading_msg="Applying saved changes...",
        ok_text="Changes applied."
    )


def test_git_stash_apply_success_with_id(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Applied stash")
    result = git_stash_apply(stash_id="2")
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "apply", "stash@{2}"],
        loading_msg="Applying saved changes...",
        ok_text="Changes applied."
    )


def test_git_stash_apply_failure(mocker):
    fake_run = mocker.patch(
        "pygitgo.commands.stash.run_command",
        side_effect=GitCommandError(["git", "stash", "apply"])
    )
    result = git_stash_apply()
    assert result is False


def test_git_stash_drop_success_no_id(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Dropped stash")
    result = git_stash_drop()
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "drop"],
        loading_msg="Cleaning up stash...",
        ok_text="Stash cleaned up."
    )


def test_git_stash_drop_success_with_id(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Dropped stash")
    result = git_stash_drop(stash_id="1")
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "drop", "stash@{1}"],
        loading_msg="Cleaning up stash...",
        ok_text="Stash cleaned up."
    )


def test_git_stash_drop_failure(mocker):
    fake_run = mocker.patch(
        "pygitgo.commands.stash.run_command",
        side_effect=GitCommandError(["git", "stash", "drop"])
    )
    result = git_stash_drop()
    assert result is False


def test_git_stash_list_success(mocker):
    stash_list_output = "stash@{0}||2026-06-01 10:00:00||Auto-Save\nstash@{1}||2026-06-01 10:05:00||My-State"
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value=stash_list_output)
    result = git_stash_list()
    assert result == stash_list_output
    fake_run.assert_called_once_with(
        [
            "git", "stash", "list",
            "--date=format:%Y-%m-%d %H:%M:%S",
            "--pretty=%gd||%cd||%s"
        ],
        loading_msg="Fetching stash list...",
        ok_text="Stash list fetched."
    )


def test_git_stash_list_failure(mocker):
    fake_run = mocker.patch(
        "pygitgo.commands.stash.run_command",
        side_effect=GitCommandError(["git", "stash", "list"])
    )
    result = git_stash_list()
    assert result == ""


def test_git_stash_clear_success(mocker):
    fake_run = mocker.patch("pygitgo.commands.stash.run_command", return_value="Cleared all stashes")
    result = git_stash_clear()
    assert result is True
    fake_run.assert_called_once_with(
        ["git", "stash", "clear"],
        loading_msg="Clearing all stashes...",
        ok_text="All stashes cleared."
    )


def test_git_stash_clear_failure(mocker):
    fake_run = mocker.patch(
        "pygitgo.commands.stash.run_command",
        side_effect=GitCommandError(["git", "stash", "clear"])
    )
    result = git_stash_clear()
    assert result is False

from pygitgo.commands.push import push_operation
from pygitgo.exceptions import GitGoError
from argparse import Namespace
import pytest


def test_push_new_branch_flag_no_name():
    args = Namespace(branch=None, message="Init commit", new=True, select=False)
    with pytest.raises(GitGoError) as exc_info:
        push_operation(args)
    assert "Branch name required when using --new flag!" in str(exc_info.value)


def test_push_new_branch_success(mocker):
    fake_new_branch = mocker.patch("pygitgo.commands.push.git_new_branch")
    fake_commit = mocker.patch("pygitgo.commands.push.git_commit", return_value=True)
    fake_push = mocker.patch("pygitgo.commands.push.git_push")
    mocker.patch("pygitgo.commands.push.print_banner")

    args = Namespace(branch="feature-branch", message="Init commit", new=True, select=False)
    push_operation(args)

    fake_new_branch.assert_called_once_with("feature-branch")
    fake_commit.assert_called_once_with("Init commit")
    fake_push.assert_called_once_with("feature-branch")


def test_push_wrong_branch_auto_switch(mocker):
    mocker.patch("pygitgo.commands.push.is_branch_exist", return_value=True)
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    fake_info = mocker.patch("pygitgo.commands.push.info")
    fake_jump = mocker.patch("pygitgo.commands.push.jump_operation")
    fake_commit = mocker.patch("pygitgo.commands.push.git_commit", return_value=True)
    fake_push = mocker.patch("pygitgo.commands.push.git_push")
    mocker.patch("pygitgo.commands.push.print_banner")

    args = Namespace(branch="feature-branch", message="Init commit", new=False, select=False)
    push_operation(args)

    fake_info.assert_any_call("Switching to target branch 'feature-branch'...")
    fake_info.assert_any_call("Switched from 'main' to 'feature-branch' automatically.")
    fake_info.assert_any_call("Run 'gitgo undo commit' then 'gitgo jump main' to revert this push and return.")
    jump_args = fake_jump.call_args[0][0]
    assert jump_args.branch == "feature-branch"
    fake_commit.assert_called_once_with("Init commit")
    fake_push.assert_called_once_with("feature-branch")


def test_push_default_branch_and_msg(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.get_config", return_value="Default Msg")
    mocker.patch("pygitgo.commands.push.info")
    fake_commit = mocker.patch("pygitgo.commands.push.git_commit", return_value=True)
    fake_push = mocker.patch("pygitgo.commands.push.git_push")
    mocker.patch("pygitgo.commands.push.print_banner")

    args = Namespace(branch=None, message=None, new=False, select=False)
    push_operation(args)

    fake_commit.assert_called_once_with("Default Msg")
    fake_push.assert_called_once_with("main")


def test_push_select_clean(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.get_changed_files", return_value=[])
    fake_info = mocker.patch("pygitgo.commands.push.info")
    fake_warning = mocker.patch("pygitgo.commands.push.warning")

    args = Namespace(branch=None, message="Selective push", new=False, select=True)
    push_operation(args)

    fake_info.assert_called_once_with("\nWorking tree is clean. Nothing to select.")
    fake_warning.assert_called_once_with("Make some changes first before using GitGo to commit and push.")


def test_push_select_no_files_chosen(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.get_changed_files", return_value=["file1.txt", "file2.txt"])
    mocker.patch("pygitgo.commands.push.display_file_picker", return_value=[])
    fake_info = mocker.patch("pygitgo.commands.push.info")

    args = Namespace(branch=None, message="Selective push", new=False, select=True)
    push_operation(args)

    fake_info.assert_called_once_with("\nNo files selected. Push aborted.\n")


def test_push_select_success(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.get_changed_files", return_value=["file1.txt", "file2.txt"])
    mocker.patch("pygitgo.commands.push.display_file_picker", return_value=["file1.txt"])
    fake_stage = mocker.patch("pygitgo.commands.push.selective_stage")
    fake_commit = mocker.patch("pygitgo.commands.push.git_commit", return_value=True)
    fake_push = mocker.patch("pygitgo.commands.push.git_push")
    mocker.patch("pygitgo.commands.push.print_banner")

    args = Namespace(branch=None, message="Selective push", new=False, select=True)
    push_operation(args)

    fake_stage.assert_called_once_with(["file1.txt"])
    fake_commit.assert_called_once_with("Selective push", loading_msg="Commiting selected files...", skip_staging=True)
    fake_push.assert_called_once_with("main")


def test_push_clean_but_unpushed_commits(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.git_commit", return_value=False) 
    fake_run = mocker.patch("pygitgo.commands.push.run_command", return_value="abc1234 Unpushed commit message\n")
    fake_warning = mocker.patch("pygitgo.commands.push.warning")
    fake_push = mocker.patch("pygitgo.commands.push.git_push")
    mocker.patch("pygitgo.commands.push.print_banner")

    args = Namespace(branch=None, message="Commit message", new=False, select=False)
    push_operation(args)

    fake_run.assert_any_call(["git", "log", "--oneline", "origin/main..HEAD"], loading_msg="Checking for unpushed commits...")
    fake_warning.assert_called_once_with("\nNo changes to commit, but found unpushed commits. Pushing to remote...")
    fake_push.assert_called_once_with("main")


def test_push_clean_and_up_to_date(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.git_commit", return_value=False) 
    fake_run = mocker.patch("pygitgo.commands.push.run_command", return_value="") 
    fake_info = mocker.patch("pygitgo.commands.push.info")
    fake_warning = mocker.patch("pygitgo.commands.push.warning")
    fake_push = mocker.patch("pygitgo.commands.push.git_push")

    args = Namespace(branch=None, message="Commit message", new=False, select=False)
    push_operation(args)

    fake_run.assert_any_call(["git", "log", "--oneline", "origin/main..HEAD"], loading_msg="Checking for unpushed commits...")
    fake_info.assert_called_once_with("\nWorking tree is clean and everything is up to date.")
    fake_warning.assert_called_once_with("Make some changes first before using GitGo to commit and push.")
    fake_push.assert_not_called()


def test_push_keyboard_interrupt_no_changes_made(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.git_commit", side_effect=KeyboardInterrupt)
    fake_run = mocker.patch("pygitgo.commands.push.run_command")
    fake_run.return_value = "initial_hash" 
    fake_warning = mocker.patch("pygitgo.commands.push.warning")
    fake_info = mocker.patch("pygitgo.commands.push.info")

    fake_run.side_effect = lambda cmd, *a, **kw: "" if cmd == ["git", "status", "--porcelain"] else "initial_hash"

    args = Namespace(branch=None, message="Commit message", new=False, select=False)
    with pytest.raises(SystemExit) as sys_exit:
        push_operation(args)

    assert sys_exit.value.code == 130
    fake_warning.assert_any_call("Push interrupted (Ctrl+C).")


def test_push_keyboard_interrupt_commit_made(mocker):
    mocker.patch("pygitgo.commands.push.get_current_branch", return_value="main")
    mocker.patch("pygitgo.commands.push.git_commit", return_value=True)
    mocker.patch("pygitgo.commands.push.git_push", side_effect=KeyboardInterrupt)
    
    fake_run = mocker.patch("pygitgo.commands.push.run_command")
    fake_run.side_effect = ["old_hash", "new_hash"] # first call: initial rev-parse HEAD. second call: post-cleanup check.
    
    fake_warning = mocker.patch("pygitgo.commands.push.warning")
    fake_info = mocker.patch("pygitgo.commands.push.info")

    args = Namespace(branch=None, message="Commit message", new=False, select=False)
    with pytest.raises(SystemExit) as sys_exit:
        push_operation(args)

    assert sys_exit.value.code == 130
    fake_warning.assert_any_call("Push interrupted (Ctrl+C).")
    fake_info.assert_any_call("Commit was saved locally on 'main' but was not pushed.")



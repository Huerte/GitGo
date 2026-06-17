from pygitgo.commands.git_branch import (
    git_new_branch, get_current_branch, is_branch_exist
)
import pytest


def test_git_branch_logic(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_branch.run_command")

    branch_name = "hello-world"
    result = git_new_branch(branch_name)
    assert result == "hello-world"

    fake_run.assert_called_once_with(
        ["git", "checkout", "-b", "hello-world"], 
        loading_msg="Creating branch 'hello-world'...",
        ok_text="Branch 'hello-world' created."
    )

def test_git_branch_exists_jump_yes(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main") 
    mocker.patch("builtins.input", return_value="y")
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")
    fake_error = mocker.patch("pygitgo.commands.git_branch.error")

    branch_name = "existing-branch"
    result = git_new_branch(branch_name)

    assert result == "existing-branch"
    fake_error.assert_called_once_with(f"Failed to create branch '{branch_name}'. It may already exist.")

    args = fake_jump.call_args[0][0]
    assert args.branch == branch_name


def test_git_branch_exists_jump_no(mocker):
    from pygitgo.exceptions import GitCommandError, GitGoError
    fake_run = mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main") 
    mocker.patch("builtins.input", return_value="n")
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")
    fake_error = mocker.patch("pygitgo.commands.git_branch.error")

    branch_name = "existing-branch"

    with pytest.raises(GitGoError):
        git_new_branch(branch_name)
    fake_error.assert_called_once_with(f"Failed to create branch '{branch_name}'. It may already exist.")
    fake_jump.assert_not_called()


def test_git_branch_already_on_target_skips_prompt(mocker):
    from pygitgo.exceptions import GitCommandError
    mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="feat/safe-interruptions")
    fake_info = mocker.patch("pygitgo.commands.git_branch.info", create=True)
    fake_input = mocker.patch("builtins.input")
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")

    result = git_new_branch("feat/safe-interruptions")

    assert result == "feat/safe-interruptions"
    fake_input.assert_not_called()
    fake_jump.assert_not_called() 
    fake_info.assert_called_once_with("Already on branch 'feat/safe-interruptions'. Continuing...")

def test_get_current_branch(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_branch.run_command", return_value='main')

    result = get_current_branch()
    assert result == 'main'

    fake_run.assert_called_once_with(
        ['git', 'branch', '--show-current']
    )

def test_is_branch_exist_true(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_branch.run_command',
        return_value=True
    )

    result = is_branch_exist('main')
    assert result == True

    fake_run.assert_called_once_with(
        ["git", "branch", "-r", "--list", "*/main"]
    )

def test_is_branch_exist_false(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_branch.run_command',
        return_value=False
    )

    result = is_branch_exist('not-exist')
    assert result == False

    fake_run.assert_called_with(
        ["git", "branch", "--list", 'not-exist']
    )

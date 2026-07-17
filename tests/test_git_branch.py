from pygitgo.commands.git_branch import (
    git_new_branch, get_current_branch, is_branch_exist, get_main_branch, get_head_sha
)
from pygitgo.exceptions import GitCommandError, GitGoError
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
    fake_run = mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main") 
    mocker.patch("pygitgo.commands.git_branch.confirm", return_value=True)
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")
    fake_error = mocker.patch("pygitgo.commands.git_branch.error")

    branch_name = "existing-branch"
    result = git_new_branch(branch_name)

    assert result == "existing-branch"
    fake_error.assert_called_once_with(f"Failed to create branch '{branch_name}'. It may already exist.")
    args = fake_jump.call_args[0][0]
    assert args.branch == branch_name

def test_git_branch_exists_jump_no(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main") 
    mocker.patch("pygitgo.commands.git_branch.confirm", return_value=False)
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")
    fake_error = mocker.patch("pygitgo.commands.git_branch.error")

    branch_name = "existing-branch"
    with pytest.raises(GitGoError):
        git_new_branch(branch_name)
    fake_error.assert_called_once_with(f"Failed to create branch '{branch_name}'. It may already exist.")
    fake_jump.assert_not_called()

def test_git_branch_already_on_target_skips_prompt(mocker):
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
    fake_run.assert_called_once_with(['git', 'branch', '--show-current'])

def test_is_branch_exist_true(mocker):
    fake_run = mocker.patch('pygitgo.commands.git_branch.run_command', return_value="origin/main")
    result = is_branch_exist('main')
    assert result is True

def test_is_branch_exist_false(mocker):
    fake_run = mocker.patch('pygitgo.commands.git_branch.run_command', return_value="")
    result = is_branch_exist('not-exist')
    assert result is False

def test_get_current_branch_detached_head(mocker):
    mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=["", "abcdef0"])
    assert get_current_branch(safe=False) == "abcdef0"

def test_get_current_branch_detached_head_safe_confirm_yes(mocker):
    mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=["", "abcdef0", ""])
    mocker.patch("pygitgo.commands.git_branch.confirm", return_value=True)
    mocker.patch("builtins.input", return_value="save-branch")
    assert get_current_branch(safe=True) == "save-branch"

def test_get_current_branch_detached_head_safe_confirm_no(mocker):
    mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=["", "abcdef0"])
    mocker.patch("pygitgo.commands.git_branch.confirm", return_value=False)
    with pytest.raises(GitGoError):
        get_current_branch(safe=True)

def test_get_main_branch_default(mocker):
    mocker.patch("pygitgo.commands.git_branch.get_config", return_value="main")
    mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["cmd"]))
    assert get_main_branch() == "main"

def test_get_main_branch_remote_invalid(mocker):
    mocker.patch("pygitgo.commands.git_branch.get_config", return_value="main")
    mocker.patch("pygitgo.commands.git_branch.run_command", return_value="some other output")
    assert get_main_branch() == "main"

def test_get_main_branch_remote_valid(mocker):
    mocker.patch("pygitgo.commands.git_branch.get_config", return_value="main")
    mocker.patch("pygitgo.commands.git_branch.run_command", return_value="* remote origin\n  HEAD branch: dev\n")
    assert get_main_branch() == "dev"

def test_get_head_sha(mocker):
    mocker.patch("pygitgo.commands.git_branch.run_command", return_value="abcdef0123456789")
    assert get_head_sha(short=False) == "abcdef0123456789"
    assert get_head_sha(short=True) == "abcdef0123456789"

def test_git_new_branch_current_branch_fails(mocker):
    mocker.patch("pygitgo.commands.git_branch.run_command", side_effect=GitCommandError(["checkout"]))
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", side_effect=Exception("failed"))
    mocker.patch("pygitgo.commands.git_branch.confirm", return_value=True)
    mocker.patch("pygitgo.commands.jump.jump_operation")
    assert git_new_branch("feat") == "feat"

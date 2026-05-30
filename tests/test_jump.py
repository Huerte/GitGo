from pygitgo.commands.jump import undo_jump_operation, jump_operation
from pygitgo.exceptions import GitCommandError, GitGoError
from conftest import capture_system_exit_code
from argparse import Namespace
import pytest


def make_args(branch):
    return Namespace(branch=branch)

def test_undo_jump_operation_no_stash(mocker):
    fake_run = mocker.patch('pygitgo.commands.jump.run_command', return_value='')
    fake_pop = mocker.patch('pygitgo.commands.jump.git_stash_pop', return_value=True)

    undo_jump_operation("original_branch", False)

    fake_run.assert_any_call(
        ["git", "reset", "--hard", "HEAD"],
        loading_msg="Canceling... Putting your files back exactly how they were..."
    )
    fake_run.assert_any_call(
        ['git', 'checkout', "original_branch"],
        loading_msg="Jumping you back to the original branch 'original_branch'..."
    )
    fake_pop.assert_not_called()


def test_undo_jump_operation_with_stash(mocker):
    fake_run = mocker.patch('pygitgo.commands.jump.run_command', return_value='')
    fake_pop = mocker.patch('pygitgo.commands.jump.git_stash_pop', return_value=True)

    undo_jump_operation("original_branch", True)

    fake_run.assert_any_call(
        ["git", "reset", "--hard", "HEAD"],
        loading_msg="Canceling... Putting your files back exactly how they were..."
    )
    fake_run.assert_any_call(
        ['git', 'checkout', "original_branch"],
        loading_msg="Jumping you back to the original branch 'original_branch'..."
    )
    fake_pop.assert_called_once()


def test_undo_jump_operation_deletes_ghost_branch(mocker):
    fake_run = mocker.patch('pygitgo.commands.jump.run_command', return_value='')
    fake_pop = mocker.patch('pygitgo.commands.jump.git_stash_pop', return_value=True)

    undo_jump_operation("original_branch", True, created_branch="ghost-branch")

    fake_run.assert_any_call(
        ['git', 'checkout', "original_branch"],
        loading_msg="Jumping you back to the original branch 'original_branch'..."
    )
    fake_run.assert_any_call(
        ["git", "branch", "-D", "ghost-branch"],
        allow_fail=True,
        loading_msg="Removing the empty branch 'ghost-branch'..."
    )
    fake_pop.assert_called_once()


def test_jump_operation_same_branch(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='main')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')

    assert capture_system_exit_code(lambda: jump_operation(make_args('main'))) == 0
    fake_warning.assert_called_with("\nYou are already on branch 'main'.\n")


def test_jump_operation_not_valid_repo(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.warning')
    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=GitCommandError(['git', 'status'], stderr='not a repo', returncode=128)
    )

    assert capture_system_exit_code(lambda: jump_operation(make_args('main'))) == 1


def test_jump_operation_has_changes_exit(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    mocker.patch('builtins.input', side_effect=['n'])
    mocker.patch('pygitgo.commands.jump.run_command', return_value='M file.txt')

    assert capture_system_exit_code(lambda: jump_operation(make_args('main'))) == 0
    fake_warning.assert_any_call("\nYou cannot switch branches with unsaved changes. Jump canceled.\n")


def test_jump_operation_no_changes(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    fake_success = mocker.patch('pygitgo.commands.jump.success')
    mocker.patch('pygitgo.commands.jump.run_command', side_effect=['', 'ok', 'ok'])

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0

    fake_success.assert_called_with("\nSuccess! You are now on 'feature'.\n")


def test_jump_operation_save_changes_error(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    mocker.patch('builtins.input', return_value='y')

    mocker.patch('pygitgo.commands.jump.run_command', return_value='M file.txt')
    mocker.patch(
        'pygitgo.commands.jump.git_stash_push',
        return_value=False
    )

    assert capture_system_exit_code(lambda: jump_operation(make_args('main'))) == 1
    fake_warning.assert_called_with(
        "\nFailed to save your changes. Please resolve any issues and try again."
    )



def test_jump_operation_branch_not_exist_cancel_operation(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=False)
    mocker.patch('builtins.input', side_effect=['y', 'n'])

    fake_info = mocker.patch('pygitgo.commands.jump.info')
    mocker.patch('pygitgo.commands.jump.run_command', return_value='M file.txt')
    mocker.patch('pygitgo.commands.jump.git_stash_push', return_value=True)
    fake_pop = mocker.patch('pygitgo.commands.jump.git_stash_pop', return_value=True)

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0

    fake_info.assert_any_call('\nYour changes have been saved. Jumping to the new branch...')
    fake_info.assert_any_call("Exiting without jumping...\n")
    fake_pop.assert_called_once()


def test_jump_operation_branch_not_exist_create_branch(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=False)
    mocker.patch('pygitgo.commands.jump.git_new_branch', return_value=None)
    mocker.patch('builtins.input', side_effect=['y', 'y'])

    fake_success = mocker.patch('pygitgo.commands.jump.success')
    fake_info = mocker.patch('pygitgo.commands.jump.info')

    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *a, **kw: 'M file.txt' if a[0] == ['git', 'status', '--porcelain'] else 'ok'
    )
    mocker.patch('pygitgo.commands.jump.git_stash_push', return_value=True)
    fake_apply = mocker.patch('pygitgo.commands.jump.git_stash_apply', return_value=True)
    fake_drop = mocker.patch('pygitgo.commands.jump.git_stash_drop', return_value=True)

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0

    fake_info.assert_called_with('\nYour changes have been saved. Jumping to the new branch...')
    fake_success.assert_any_call("\nSuccess! You are now on 'feature'.")
    fake_success.assert_any_call("Your unsaved code was moved here safely!\n")
    fake_apply.assert_called_once()
    fake_drop.assert_called_once()


def test_jump_operation_sync_fail_cancel(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('pygitgo.commands.jump.undo_jump_operation', return_value=None)
    mocker.patch('builtins.input', side_effect=['n'])   # "stay?" → no

    fake_warning = mocker.patch('pygitgo.commands.jump.warning')

    def _run(*args, **kwargs):
        cmd = args[0]
        if cmd == ['git', 'status', '--porcelain']:
            return ''
        if cmd[1] == 'pull':
            return GitCommandError(cmd, stderr='failed', returncode=1)
        return 'ok'

    mocker.patch('pygitgo.commands.jump.run_command', side_effect=_run)

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 1
    fake_warning.assert_any_call(
        "\nFailed to pull updates from 'main'. Make sure you have internet or the remote branch exists."
    )


def test_jump_operation_sync_fail_stay(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('builtins.input', side_effect=['y'])   # "stay?" → yes

    fake_success = mocker.patch('pygitgo.commands.jump.success')

    def _run(*args, **kwargs):
        cmd = args[0]
        if cmd == ['git', 'status', '--porcelain']:
            return ''
        if cmd[1] == 'pull':
            return GitCommandError(cmd, stderr='failed', returncode=1)
        return 'ok'

    mocker.patch('pygitgo.commands.jump.run_command', side_effect=_run)

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0
    fake_success.assert_any_call(
        "\nOkay! You are on the new branch, but without the latest updates from 'main'."
    )



def test_jump_operation_merge_conflict_cancel(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('pygitgo.commands.jump.undo_jump_operation', return_value=None)
    mocker.patch('builtins.input', side_effect=['y', 'n'])

    fake_error = mocker.patch('pygitgo.commands.jump.error')

    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *a, **kw: 'M file.txt' if a[0] == ['git', 'status', '--porcelain'] else 'ok'
    )
    mocker.patch('pygitgo.commands.jump.git_stash_push', return_value=True)
    mocker.patch(
        'pygitgo.commands.jump.git_stash_apply',
        return_value=False
    )

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0
    fake_error.assert_any_call("\nSTOP! There is a 'Merge Conflict'.")


def test_jump_operation_merge_conflict_stay(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('builtins.input', side_effect=['y', 'y'])

    fake_success = mocker.patch('pygitgo.commands.jump.success')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    fake_info = mocker.patch('pygitgo.commands.jump.info')

    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *a, **kw: 'M file.txt' if a[0] == ['git', 'status', '--porcelain'] else 'ok'
    )
    mocker.patch('pygitgo.commands.jump.git_stash_push', return_value=True)
    mocker.patch(
        'pygitgo.commands.jump.git_stash_apply',
        return_value=False
    )
    fake_drop = mocker.patch('pygitgo.commands.jump.git_stash_drop', return_value=True)

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0

    fake_success.assert_any_call("\nOkay! You are on the new branch with your code.")
    fake_warning.assert_any_call("Please open your code editor RIGHT NOW to fix the conflicts!")
    fake_info.assert_any_call("Your stash backup is still saved. Run 'gitgo state list' to see it.\n")
    fake_drop.assert_not_called()

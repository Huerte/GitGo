from pygitgo.commands.jump import undo_jump_operation, jump_operation
from pygitgo.exceptions import GitCommandError
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
        loading_msg="Canceling... Putting your files back exactly how they were...",
        ok_text="Files restored to original state."
    )
    fake_run.assert_any_call(
        ['git', 'checkout', "original_branch"],
        loading_msg="Jumping you back to the original branch 'original_branch'...",
        ok_text="Canceled safely. Back on 'original_branch'."
    )
    fake_pop.assert_not_called()


def test_undo_jump_operation_with_stash(mocker):
    fake_run = mocker.patch('pygitgo.commands.jump.run_command', return_value='')
    fake_pop = mocker.patch('pygitgo.commands.jump.git_stash_pop', return_value=True)

    undo_jump_operation("original_branch", True)

    fake_run.assert_any_call(
        ["git", "reset", "--hard", "HEAD"],
        loading_msg="Canceling... Putting your files back exactly how they were...",
        ok_text="Files restored to original state."
    )
    fake_run.assert_any_call(
        ['git', 'checkout', "original_branch"],
        loading_msg="Jumping you back to the original branch 'original_branch'...",
        ok_text=None
    )
    fake_pop.assert_called_once_with(ok_text="Canceled safely. Back on 'original_branch'. Your code is safe.")


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
        loading_msg="Removing the empty branch 'ghost-branch'...",
        ok_text=None
    )
    fake_pop.assert_called_once_with(ok_text="Canceled safely. Back on 'original_branch'. Your code is safe.")


def test_jump_operation_same_branch(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='main')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')

    assert capture_system_exit_code(lambda: jump_operation(make_args('main'))) == 0
    fake_warning.assert_called_with("Already on branch 'main'.")


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
    fake_warning.assert_any_call("You cannot switch branches with unsaved edits. Jump canceled.")


def test_jump_operation_has_changes_moves_to_branch(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('builtins.input', return_value='y')
    fake_info = mocker.patch('pygitgo.commands.jump.info')
    fake_success = mocker.patch('pygitgo.commands.jump.success')
    mocker.patch('pygitgo.commands.jump.git_stash_push', return_value=True)
    mocker.patch('pygitgo.commands.jump.git_stash_apply', return_value=True)
    fake_drop = mocker.patch('pygitgo.commands.jump.git_stash_drop', return_value=True)
    mocker.patch('pygitgo.commands.jump.run_command', side_effect=lambda *a, **kw: 'M file.txt' if a[0] == ['git', 'status', '--porcelain'] else 'ok')

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0
    fake_info.assert_any_call("Changes saved. Jumping to the new branch...")
    fake_drop.assert_called_once_with(loading_msg="Cleaning up the temporary stash...", ok_text="On 'feature'. Your changes came with you.")
    fake_success.assert_not_called()


def test_jump_operation_no_changes(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    fake_success = mocker.patch('pygitgo.commands.jump.success')
    mocker.patch('pygitgo.commands.jump.run_command', side_effect=['', 'ok', 'ok'])

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0

    fake_success.assert_not_called()



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
    fake_warning.assert_called_with("Stash failed. Your working tree may have untracked files.")


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

    fake_info.assert_any_call("Changes saved. Jumping to the new branch...")
    fake_info.assert_any_call("Exiting without jumping...")
    fake_pop.assert_called_once_with(loading_msg="Putting your unsaved changes back...")


def test_jump_operation_branch_not_exist_create_branch(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=False)
    fake_new_branch = mocker.patch('pygitgo.commands.jump.git_new_branch', return_value=None)
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

    fake_info.assert_any_call("Changes saved. Jumping to the new branch...")
    fake_new_branch.assert_called_once_with('feature', ok_text="Branch 'feature' created.")
    fake_success.assert_not_called()
    fake_apply.assert_called_once()
    fake_drop.assert_called_once_with(loading_msg="Cleaning up the temporary stash...", ok_text="On 'feature'. Your changes came with you.")


def test_jump_operation_sync_fail_stay(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)

    fake_info = mocker.patch('pygitgo.commands.jump.info')

    def _run(*args, **kwargs):
        cmd = args[0]
        if cmd == ['git', 'status', '--porcelain']:
            return ''
        if cmd[1] == 'pull':
            raise GitCommandError(cmd, stderr='failed', returncode=1)
        return 'ok'

    mocker.patch('pygitgo.commands.jump.run_command', side_effect=_run)

    assert capture_system_exit_code(lambda: jump_operation(make_args('feature'))) == 0
    fake_info.assert_any_call(
        "On 'feature', but without the latest updates from 'main'."
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
    fake_error.assert_any_call("MERGE CONFLICT — your changes clash with the target branch.")


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

    fake_success.assert_any_call("On 'feature'. Conflict markers are in your files.")
    fake_warning.assert_any_call("Open your editor and fix the conflict lines.")
    fake_info.assert_any_call("Your stash backup is still saved. Run 'gitgo state list' to see it.")
    fake_drop.assert_not_called()


def test_jump_keyboard_interrupt_during_checkout(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mock_warning = mocker.patch('pygitgo.commands.jump.warning')
    mock_cleanup = mocker.patch('pygitgo.commands.jump._jump_interrupt_cleanup')

    def side_effect(cmd, *args, **kwargs):
        if cmd == ['git', 'status', '--porcelain']:
            return ''
        if cmd == ['git', 'checkout', 'feature']:
            raise KeyboardInterrupt()
        return 'ok'

    mocker.patch('pygitgo.commands.jump.run_command', side_effect=side_effect)

    with pytest.raises(SystemExit) as exc_info:
        jump_operation(make_args('feature'))

    assert exc_info.value.code == 130
    mock_warning.assert_called_with("Jump interrupted (Ctrl+C).")
    mock_cleanup.assert_called_once_with('main', False, None)


def test_jump_keyboard_interrupt_after_stash(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist', return_value=True)
    mocker.patch('pygitgo.commands.jump.get_main_branch', return_value='main')
    mocker.patch('pygitgo.commands.jump.confirm', return_value=True)
    mocker.patch('pygitgo.commands.jump.git_stash_push', return_value=True)
    mock_cleanup = mocker.patch('pygitgo.commands.jump._jump_interrupt_cleanup')

    def side_effect(cmd, *args, **kwargs):
        if cmd == ['git', 'status', '--porcelain']:
            return 'M file.txt'
        if cmd[0] == 'git' and cmd[1] == 'checkout':
            raise KeyboardInterrupt()
        return 'ok'

    mocker.patch('pygitgo.commands.jump.run_command', side_effect=side_effect)

    with pytest.raises(SystemExit) as exc_info:
        jump_operation(make_args('feature'))

    assert exc_info.value.code == 130
    mock_cleanup.assert_called_once_with('main', True, None)

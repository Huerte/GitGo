from pygitgo.commands.jump import undo_jump_operation, jump_operation
import subprocess
import pytest

def check_pytest_system_exit(function):
    with pytest.raises(SystemExit) as exc_info:
        function()

    return exc_info.value.code

def test_undo_jump_operation_no_changes(mocker):
    mocker.patch('pygitgo.commands.jump.run_command', return_value="")
        
    assert check_pytest_system_exit(lambda: undo_jump_operation("original_branch", "")) == 0

def test_undo_jump_operation_has_changes(mocker):
    fake_run = mocker.patch('pygitgo.commands.jump.run_command', side_effect=["", None, None])
    
    undo_jump_operation("original_branch", "some changes")
    
    fake_run.assert_any_call(["git", "reset", "--hard", "HEAD"], loading_msg="Canceling... Putting your files back exactly how they were...")
    fake_run.assert_any_call(['git', 'checkout', "original_branch"], loading_msg=f"Jumping you back to the original branch 'original_branch'...")
    fake_run.assert_any_call(["git", "stash", "pop"], loading_msg="Restoring your unsaved changes...")

def test_jump_operation_help(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.jump.jump_operations_help', 
        return_value=''
    )
    
    assert check_pytest_system_exit(lambda: jump_operation(['-h'])) == 0

def test_jump_operation_same_branch(mocker):
    main_branch = 'main'
    fake_run = mocker.patch(
        'pygitgo.commands.jump.get_current_branch', 
        return_value=main_branch
    )
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')

    assert check_pytest_system_exit(lambda: jump_operation([main_branch])) == 0

    fake_warning.assert_called_with(f"\nYou are already on branch '{main_branch}'.\n")

def test_jump_operation_not_valid_repo(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')

    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command', 
        return_value=subprocess.CalledProcessError(1, 'git')
    )
    
    assert check_pytest_system_exit(lambda: jump_operation(['main'])) == 1

    fake_warning.assert_called_with("\nUnable to check for uncommitted changes. Please ensure you're in a valid git repository.")

    fake_run.assert_any_call(['git', 'status', '--porcelain'], allow_fail=True)

def test_jump_operation_has_changes_exit(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=True)
    
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    fake_success = mocker.patch('pygitgo.commands.jump.success')
    mocker.patch('builtins.input',side_effect=['n'])
    
    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=['some-changes', 'ok', 'ok']
    )

    assert check_pytest_system_exit(lambda: jump_operation(['main'])) == 0

    fake_warning.assert_any_call("\nOkay! Leaving your changes here. Jumping without them...\n")
    fake_success.assert_any_call("\nSuccess! You are now on 'main'.\n")
    
    fake_run.assert_any_call(['git', 'status', '--porcelain'], allow_fail=True)
    fake_run.assert_any_call(['git', 'checkout', 'main'], loading_msg="Moving you to branch 'main'...")
    fake_run.assert_any_call(['git', 'pull', 'origin', 'main'], allow_fail=True, loading_msg="Downloading the latest updates from 'main'...")

def test_jump_operation_save_changes_error(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    mocker.patch('builtins.input', return_value='y')
    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *args, **kwargs: (
            'ok' if args[0] != ["git", "stash", "push", "-m", "GitGo Jump Auto-Stash"] else 
            subprocess.CalledProcessError(1, 'git')
        )
    )

    assert check_pytest_system_exit(lambda: jump_operation(['main'])) == 1

    fake_warning.assert_called_with("\nFailed to save your changes. Please resolve any issues and try again.")
    fake_run.assert_any_call(['git', 'status', '--porcelain'], allow_fail=True)
    fake_run.assert_any_call(["git", "stash", "push", "-m", "GitGo Jump Auto-Stash"], allow_fail=True, loading_msg="Saving your changes before jumping...")

def test_jump_operation_no_changes(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=True)
    fake_success = mocker.patch('pygitgo.commands.jump.success')
    mocker.patch('builtins.input', return_value='y')
    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=[
            '', 'ok', 'ok'
        ]
    )

    target_branch = 'feature'
    
    assert check_pytest_system_exit(lambda: jump_operation([target_branch])) == 0

    fake_success.assert_called_with(f"\nSuccess! You are now on '{target_branch}'.\n")
    fake_run.assert_any_call(['git', 'status', '--porcelain'], allow_fail=True)
    fake_run.assert_any_call(['git', 'checkout', target_branch], loading_msg=f"Moving you to branch '{target_branch}'...")
    fake_run.assert_any_call(['git', 'pull', 'origin', 'main'], allow_fail=True, loading_msg=f"Downloading the latest updates from 'main'...")

def test_jump_operation_branch_not_exist_cancel_operation(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=False)
    mocker.patch(
        'builtins.input', 
        side_effect=['y', 'n']
    )

    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    fake_info = mocker.patch('pygitgo.commands.jump.info')

    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=[
            'ok', 'ok', 'ok', 'ok'
        ]
    )

    target_branch = 'feature'
    
    assert check_pytest_system_exit(lambda: jump_operation([target_branch])) == 0

    fake_info.assert_any_call('\nYour changes have been saved. Jumping to the new branch...')
    fake_info.assert_any_call("Exiting without jumping...\n")
    fake_run.assert_any_call(['git', 'status', '--porcelain'], allow_fail=True)
    fake_run.assert_any_call(["git", "stash", "push", "-m", "GitGo Jump Auto-Stash"], allow_fail=True, loading_msg="Saving your changes before jumping...")
    fake_run.assert_any_call(["git", "stash", "pop"], loading_msg="Putting your unsaved changes back...")

def test_jump_operation_branch_not_exist_create_branch(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=False)
    mocker.patch('pygitgo.commands.jump.git_new_branch',return_value=None)

    mocker.patch(
        'builtins.input', 
        side_effect=['y', 'y']
    )

    fake_success = mocker.patch('pygitgo.commands.jump.success')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    fake_info = mocker.patch('pygitgo.commands.jump.info')

    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=[
            'ok', 'ok', 'ok', 'ok', 'ok'
        ]
    )

    target_branch = 'feature'
    
    assert check_pytest_system_exit(lambda: jump_operation([target_branch])) == 0

    fake_info.assert_called_with('\nYour changes have been saved. Jumping to the new branch...')
    fake_success.assert_any_call(f"\nSuccess! You are now on '{target_branch}'.")
    fake_success.assert_any_call("Your unsaved code was moved here safely!\n")
    fake_run.assert_any_call(['git', 'status', '--porcelain'], allow_fail=True)
    fake_run.assert_any_call(['git', 'pull', 'origin', 'main'], allow_fail=True, loading_msg=f"Downloading the latest updates from 'main'...")
    fake_run.assert_any_call(["git", "stash", "push", "-m", "GitGo Jump Auto-Stash"], allow_fail=True, loading_msg="Saving your changes before jumping...")
    fake_run.assert_any_call(['git', 'stash', 'apply'], allow_fail=True, loading_msg="Unpacking your unsaved changes...")
    fake_run.assert_any_call(["git", "stash", "drop"], allow_fail=True, loading_msg="Cleaning up the temporary stash...")

def test_jump_operation_sync_fail_cancel(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=True)
    mocker.patch('pygitgo.commands.jump.undo_jump_operation',return_value=None)
    mocker.patch(
        'builtins.input', 
        side_effect=['y', 'n']
    )

    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *args, **kwargs: (
            subprocess.CalledProcessError(1, 'git') if args[0] == ['git', 'pull', 'origin', 'main'] else 'ok'
        )
    )

    assert check_pytest_system_exit(lambda: jump_operation(['feature'])) == 1

    fake_warning.assert_any_call("\nFailed to pull updates from 'main'. Make sure you have internet or the remote branch exists.")

def test_jump_operation_sync_fail_stay(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=True)
    mocker.patch(
        'builtins.input', 
        side_effect=['y', 'y']
    )

    fake_success = mocker.patch('pygitgo.commands.jump.success')
    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *args, **kwargs: (
            subprocess.CalledProcessError(1, 'git') if args[0] == ['git', 'pull', 'origin', 'main'] else 'ok'
        )
    )

    assert check_pytest_system_exit(lambda: jump_operation(['feature'])) == 0

    fake_success.assert_any_call("\nOkay! You are on the new branch, but without the latest updates from 'main'.")

def test_jump_operation_merge_conflict_cancel(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=True)
    mocker.patch('pygitgo.commands.jump.undo_jump_operation',return_value=None)
    mocker.patch(
        'builtins.input', 
        side_effect=['y', 'n']
    )

    fake_error = mocker.patch('pygitgo.commands.jump.error')
    mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *args, **kwargs: (
            subprocess.CalledProcessError(1, 'git') if args[0] == ['git', 'stash', 'apply'] else 'ok'
        )
    )

    assert check_pytest_system_exit(lambda: jump_operation(['feature'])) == 0

    fake_error.assert_any_call("\nSTOP! There is a 'Merge Conflict'.")

def test_jump_operation_merge_conflict_stay(mocker):
    mocker.patch('pygitgo.commands.jump.get_current_branch',return_value='master')
    mocker.patch('pygitgo.commands.jump.get_main_branch',return_value='main')
    mocker.patch('pygitgo.commands.jump.is_branch_exist',return_value=True)
    mocker.patch(
        'builtins.input', 
        side_effect=['y', 'y']
    )

    fake_success = mocker.patch('pygitgo.commands.jump.success')
    fake_warning = mocker.patch('pygitgo.commands.jump.warning')
    fake_run = mocker.patch(
        'pygitgo.commands.jump.run_command',
        side_effect=lambda *args, **kwargs: (
            subprocess.CalledProcessError(1, 'git') if args[0] == ['git', 'stash', 'apply'] else 'ok'
        )
    )

    assert check_pytest_system_exit(lambda: jump_operation(['feature'])) == 0

    fake_success.assert_any_call("\nOkay! You are on the new branch with your code.")
    fake_warning.assert_any_call("Please open your code editor RIGHT NOW to fix the conflicts!\n")
    fake_run.assert_any_call(["git", "stash", "drop"], allow_fail=True, loading_msg="Cleaning up the temporary stash...")

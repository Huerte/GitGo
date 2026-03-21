from pygitgo.commands.git_operations import (
    git_new_branch, git_commit, get_current_branch,
    git_init, create_main_branch, add_remote_origin,
    confirm_remote_link, is_branch_exist, git_push,
    handle_rebase, 
)
import subprocess
import pytest
import os

def test_git_branch_logic(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command")

    branch_name = "hello-world"
    result = git_new_branch(branch_name)
    assert result == "hello-world"

    fake_run.assert_called_once_with(
        ["git", "checkout", "-b", "hello-world"], 
        loading_msg="Creating branch 'hello-world'..."
    )

def test_git_commit(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command")\
    
    result = git_commit("Testing the commit feature")
    assert result == True

    fake_run.assert_called_with(
        ['git', 'commit', '-m', 'Testing the commit feature'],
        loading_msg="Commiting changes..."
    )

def test_get_current_branch(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command", return_value='main')

    result = get_current_branch()
    assert result == 'main'

    fake_run.assert_called_once_with(
        ['git', 'branch', '--show-current']
    )

def test_git_init_already_initialized(mocker):
    mocker.patch('os.path.isdir', return_value=True)
    fake_warning = mocker.patch('pygitgo.commands.git_operations.warning')
    fake_run = mocker.patch('pygitgo.commands.git_operations.run_command')

    result = git_init()

    assert result == True
    fake_warning.assert_called_once() 
    fake_run.assert_not_called()

def test_git_init_success(mocker):
    mocker.patch('os.path.isdir', return_value=False)
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')
    fake_run = mocker.patch('pygitgo.commands.git_operations.run_command', return_value='ok')

    result = git_init()

    assert result == True
    fake_success.assert_called_once()
    fake_run.assert_called_once_with(
        ["git", "init", "-b", 'main'], 
        allow_fail=True, 
        loading_msg="Initializing git repository..."
    )

def test_git_init_fallback(mocker):
    mocker.patch('os.path.isdir', return_value=False)
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')
    
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command', 
        return_value=subprocess.CalledProcessError(1, 'git')
    )

    result = git_init()

    assert result == True
    fake_success.assert_called_once()
    fake_run.call_count == 3

def test_create_main_branch_no_branch(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value=subprocess.CalledProcessError(1, 'git')
    )

    create_main_branch()

    fake_run.assert_called_with(
        ["git", "checkout", "-b", "main"], 
        loading_msg="Setting default branch to 'main'..."
    )

def test_create_main_branch_rename_branch(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=['master', 'none']
    )

    create_main_branch()

    fake_run.assert_called_with(
        ["git", "branch", "-m", "main"], 
        loading_msg=f"Renaming branch 'master' to 'main'..."
    )

def test_create_main_branch_is_main(mocker):
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value='main'
    )

    create_main_branch()

    fake_success.assert_called_once_with("Already on 'main' branch.")

def test_confirm_remote_link_success(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value='ok'
    )

    result = confirm_remote_link()
    assert result == True

    fake_run.assert_called_once_with(
        ["git", "ls-remote", "origin"], allow_fail=True, 
        loading_msg="Testing connection to remote..."
    )

def test_confirm_remote_link_fallback(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value=subprocess.CalledProcessError(1, 'git')
    )

    result = confirm_remote_link()
    assert result == False

    fake_run.assert_called_once_with(
        ["git", "ls-remote", "origin"], allow_fail=True, 
        loading_msg="Testing connection to remote..."
    )

def test_handle_rebase_no_conflict(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value='ok'
    )

    result = handle_rebase()
    assert result == True

    fake_run.assert_called_with(
        ["git", "status"], allow_fail=True
    )

def test_handle_rebase_conflict(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value='rebase'
    )

    with pytest.raises(SystemExit) as exc_info:
        handle_rebase()
    
    assert exc_info.value.code == 1

    fake_run.assert_called_with(
        ["git", "status"], allow_fail=True
    )

def test_handle_rebase_fallback(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value=subprocess.CalledProcessError(1, 'git')
    )

    result = handle_rebase()
    assert result == False

    fake_run.assert_called_with(
        ["git", "status"], allow_fail=True
    )

def test_is_branch_exist_true(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value=True
    )

    result = is_branch_exist('main')
    assert result == True

    fake_run.assert_called_once_with(
        ["git", "branch", "-r", "--list", "*/main"]
    )

def test_is_branch_exist_false(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value=False
    )

    result = is_branch_exist('not-exist')
    assert result == False

    fake_run.assert_called_with(
        ["git", "branch", "--list", 'not-exist']
    )

def test_add_remote_origin_switch_origin(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value='https://github.com:Huerte/GitGo'
    )
    mocker.patch('pygitgo.commands.git_operations.isinstance', return_value=False)
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')

    url = ".com:Huerte/New-GitGo.git"
    add_remote_origin(url)

    fake_success.assert_called_once_with(f"Remote origin set to: {url}")
    fake_run.asser_called_once_with(
        ["git", "remote", "set-url", "origin", url], 
        loading_msg="Updating remote URL..."
    )

def test_add_remote_origin_add_origin(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        return_value=subprocess.CalledProcessError(1, 'git')
    )
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')

    url = ".com:Huerte/New-GitGo.git"
    add_remote_origin(url)

    fake_success.assert_called_once_with(f"Remote origin set to: {url}")
    fake_run.assert_called_with(
        ["git", "remote", "add", "origin", url], 
        loading_msg="Adding remote origin..."
    )

def test_git_push_already_ssh(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            'git@github.com:user/repo.git\n', None
        ]
    )
    mocker.patch('pygitgo.commands.git_operations.is_ssh_url', return_value=True)

    branch = 'main'
    git_push(branch)

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'..."
    )

def test_git_push_no_remote(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command', 
        return_value=subprocess.CalledProcessError(1, 'git')
    )

    branch = 'main'
    git_push(branch)

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'..."
    )

def test_git_push_https_no_connection(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            'https://github.com/user/repo.git\n',
            None
        ]
    )

    mocker.patch('pygitgo.commands.git_operations.is_ssh_url', return_value=False)
    mocker.patch('pygitgo.commands.git_operations.check_connection', return_value=False)
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')
    
    branch = 'main'
    git_push(branch)

    fake_success.assert_not_called()

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'..."
    )

def test_git_push_convert_https_to_ssh(mocker):
    url = 'https://github.com/user/repo.git\n'
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            url,
            None, None
        ]
    )

    mocker.patch('pygitgo.commands.git_operations.is_ssh_url', return_value=False)
    mocker.patch('pygitgo.commands.git_operations.check_connection', return_value=True)
    mocker.patch('pygitgo.commands.git_operations.convert_https_to_ssh', return_value=url)
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')

    branch = 'main'
    git_push(branch)

    fake_run.assert_any_call(
        ["git", "remote", "set-url", "origin", url], 
        loading_msg="Converting remote from HTTPS to SSH for secure push..."
    )

    fake_success.assert_called()

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'..."
    )
    










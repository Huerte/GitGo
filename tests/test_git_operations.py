from pygitgo.commands.git_operations import (
    git_new_branch, git_commit, get_current_branch,
    git_init, create_main_branch, add_remote_origin,
    confirm_remote_link, is_branch_exist, git_push,
    handle_rebase, check_and_sync_branch
)
from unittest.mock import call
import subprocess
import pytest


def test_git_branch_logic(mocker):
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command")

    branch_name = "hello-world"
    result = git_new_branch(branch_name)
    assert result == "hello-world"

    fake_run.assert_called_once_with(
        ["git", "checkout", "-b", "hello-world"], 
        loading_msg="Creating branch 'hello-world'..."
    )

def test_git_branch_exists_jump_yes(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("builtins.input", return_value="y")
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")
    fake_error = mocker.patch("pygitgo.commands.git_operations.error")

    branch_name = "existing-branch"
    result = git_new_branch(branch_name)
    
    assert result == "existing-branch"
    fake_error.assert_called_once_with(f"Failed to create branch '{branch_name}'! It may already exist.")
    
    args = fake_jump.call_args[0][0]
    assert args.branch == branch_name

def test_git_branch_exists_jump_no(mocker):
    from pygitgo.exceptions import GitCommandError, GitGoError
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command", side_effect=GitCommandError(["git", "checkout", "-b"]))
    mocker.patch("builtins.input", return_value="n")
    fake_jump = mocker.patch("pygitgo.commands.jump.jump_operation")
    fake_error = mocker.patch("pygitgo.commands.git_operations.error")

    branch_name = "existing-branch"
    
    with pytest.raises(GitGoError):
        git_new_branch(branch_name)
    fake_error.assert_called_once_with(f"Failed to create branch '{branch_name}'! It may already exist.")
    fake_jump.assert_not_called()

def test_git_commit(mocker):
    mocker.patch("pygitgo.commands.git_operations._get_signing_flags", return_value=[])
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command")
    
    result = git_commit("Testing the commit feature")
    assert result == True

    fake_run.assert_any_call(
        ['git', 'commit', '-S', '-m', 'Testing the commit feature'],
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

    assert result == False
    fake_warning.assert_called_once() 
    fake_run.assert_not_called()

def test_git_init_success(mocker):
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('pygitgo.commands.git_operations.get_config', return_value='main')
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')
    fake_run = mocker.patch('pygitgo.commands.git_operations.run_command', return_value='ok')

    result = git_init()

    assert result == True
    fake_success.assert_called_once()
    fake_run.assert_called_once_with(
        ["git", "init", "-b", 'main'], 
        loading_msg="Initializing git repository..."
    )

def test_git_init_fallback(mocker):
    from pygitgo.exceptions import GitCommandError
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('pygitgo.commands.git_operations.get_config', return_value='main')
    fake_success = mocker.patch('pygitgo.commands.git_operations.success')
    
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command', 
        side_effect=[
            GitCommandError(["git", "init", "-b", "main"]),
            "init_success",
            "checkout_success"
        ]
    )

    result = git_init()

    assert result == True
    fake_success.assert_called_once()
    assert fake_run.call_count == 3

def test_create_main_branch_no_branch(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[GitCommandError(["git", "branch"]), "ok"]
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
        ["git", "ls-remote", "origin"], 
        loading_msg="Testing connection to remote..."
    )

def test_confirm_remote_link_fallback(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=GitCommandError(["git", "ls-remote"])
    )

    result = confirm_remote_link()
    assert result == False

    fake_run.assert_called_once_with(
        ["git", "ls-remote", "origin"], 
        loading_msg="Testing connection to remote..."
    )

def test_handle_rebase(mocker):
    from pygitgo.exceptions import GitGoError
    fake_warning = mocker.patch("pygitgo.commands.git_operations.warning")
    fake_info = mocker.patch("pygitgo.commands.git_operations.info")

    with pytest.raises(GitGoError) as exc_info:
        handle_rebase()

    assert "Push aborted — rebase conflict in progress." in str(exc_info.value)
    fake_warning.assert_called_once_with("Conflict detected during rebase.")
    assert fake_info.call_count == 4

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
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            GitCommandError(["git", "remote", "get-url"]),
            "added"
        ]
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
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command', 
        side_effect=[
            GitCommandError(["git", "remote", "get-url"]),
            "pushed"
        ]
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
    
def test_check_and_sync_branch_equal_branch(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            None,
            'main', 'main'
        ]
    )

    fake_success = mocker.patch('pygitgo.commands.git_operations.success')

    branch = 'main'
    check_and_sync_branch(branch)

    fake_success.assert_called_once_with("Branch is already up to date.")
    
    fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{branch}"])
    ]

def test_check_and_sync_branch_remote_ahead(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            None, 'main', 'master', 0
        ]
    )

    fake_success = mocker.patch('pygitgo.commands.git_operations.success')

    branch = 'main'
    remote_branch = 'master'
    check_and_sync_branch(branch)

    fake_success.assert_called_once_with("Branch is up to date.")
    
    fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{remote_branch}"]),
        call(["git", "rev-list", "--count", f"{branch}..origin/{remote_branch}"])
    ]

def test_check_and_sync_branch_need_sync(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[
            None, 'main', 'master', 1, 'ok'
        ]
    )

    fake_success = mocker.patch('pygitgo.commands.git_operations.success')

    branch = 'main'
    remote_branch = 'master'
    check_and_sync_branch(branch)

    fake_success.assert_called_once_with("Synced with remote.")
    
    fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{remote_branch}"]),
        call(["git", "rev-list", "--count", f"{branch}..origin/{remote_branch}"]),
        call(["git", "pull", "--rebase", "origin", remote_branch], loading_msg="Pulling changes from remote...")
    ]

def test_check_and_sync_branch_no_remote(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=GitCommandError(['git', 'fetch'], stderr='error', returncode=1)
    )

    fake_warning = mocker.patch('pygitgo.commands.git_operations.warning')

    check_and_sync_branch('main')

    fake_warning.assert_called_with("Could not fetch from remote. Proceeding with push...")

    fake_run.assert_called_with(
        ["git", "fetch", "origin"], 
        loading_msg="Checking if branch is up to date..."
    )

def test_check_and_sync_branch_remote_not_exist(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[None, GitCommandError(['git', 'rev-parse'], stderr='error', returncode=1)]
    )

    fake_warning = mocker.patch('pygitgo.commands.git_operations.warning')

    branch = 'main'
    check_and_sync_branch(branch)

    fake_warning.assert_called_with("Remote branch doesn't exist yet. First push will create it.")

    fake_run.assert_any_call(
        ["git", "fetch", "origin"], 
        loading_msg="Checking if branch is up to date..."
    )

    fake_run.assert_any_call(
        ["git", "rev-parse", branch]
    )

def test_git_commit_skip_staging_does_not_run_git_add(mocker):
    mocker.patch("pygitgo.commands.git_operations._get_signing_flags", return_value=[])
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command")
    
    fake_run.side_effect = ["M file.py", None]
    git_commit("my message", skip_staging=True)

    for call in fake_run.call_args_list:
        args = call[0][0]
        assert args[:2] != ["git", "add"], "git add should not run when skip_staging=True"

def test_git_commit_default_runs_git_add(mocker):
    mocker.patch("pygitgo.commands.git_operations._get_signing_flags", return_value=[])
    fake_run = mocker.patch("pygitgo.commands.git_operations.run_command")
    fake_run.side_effect = ["M file.py", None, None]
    git_commit("my message")
    add_call = fake_run.call_args_list[1][0][0]
    assert add_call == ["git", "add", "."]

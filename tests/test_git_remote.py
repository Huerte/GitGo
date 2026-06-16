from pygitgo.commands.git_remote import (
    confirm_remote_link, handle_rebase,
    add_remote_origin, check_and_sync_branch
)
from unittest.mock import call
import pytest



def test_confirm_remote_link_success(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        return_value='ok'
    )

    result = confirm_remote_link()
    assert result == True

    fake_run.assert_called_once_with(
        ["git", "ls-remote", "origin"], 
        loading_msg="Testing connection to remote...",
        ok_text="Remote is reachable."
    )

def test_confirm_remote_link_fallback(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=GitCommandError(["git", "ls-remote"])
    )

    result = confirm_remote_link()
    assert result == False

    fake_run.assert_called_once_with(
        ["git", "ls-remote", "origin"], 
        loading_msg="Testing connection to remote...",
        ok_text="Remote is reachable."
    )

def test_handle_rebase(mocker):
    from pygitgo.exceptions import GitGoError
    fake_warning = mocker.patch("pygitgo.commands.git_remote.warning")
    fake_info = mocker.patch("pygitgo.commands.git_remote.info")

    with pytest.raises(GitGoError) as exc_info:
        handle_rebase()

    assert "Push aborted — rebase conflict in progress." in str(exc_info.value)
    fake_warning.assert_called_once_with("Conflict detected during rebase.")
    assert fake_info.call_count == 4

def test_add_remote_origin_switch_origin(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        return_value='https://github.com:Huerte/GitGo'
    )
    mocker.patch('pygitgo.commands.git_remote.isinstance', return_value=False)

    url = ".com:Huerte/New-GitGo.git"
    add_remote_origin(url)

    fake_run.assert_called_with(
        ["git", "remote", "set-url", "origin", url], 
        loading_msg="Updating remote URL...",
        ok_text=f"Remote origin set to: {url}"
    )

def test_add_remote_origin_add_origin(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=[
            GitCommandError(["git", "remote", "get-url"]),
            "added"
        ]
    )

    url = ".com:Huerte/New-GitGo.git"
    add_remote_origin(url)

    fake_run.assert_called_with(
        ["git", "remote", "add", "origin", url], 
        loading_msg="Adding remote origin...",
        ok_text=f"Remote origin set to: {url}"
    )

def test_check_and_sync_branch_equal_branch(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=[
            None,
            'main', 'main'
        ]
    )

    fake_info = mocker.patch('pygitgo.commands.git_remote.info')

    branch = 'main'
    check_and_sync_branch(branch)

    fake_info.assert_called_once_with("Branch is already up to date.")
    
    assert fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{branch}"])
    ]

def test_check_and_sync_branch_remote_ahead(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=[
            None, 'main', 'master', 0
        ]
    )

    fake_info = mocker.patch('pygitgo.commands.git_remote.info')

    branch = 'main'
    check_and_sync_branch(branch)

    fake_info.assert_called_once_with("Branch is up to date.")
    
    assert fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{branch}"]),
        call(["git", "rev-list", "--count", f"{branch}..origin/{branch}"])
    ]

def test_check_and_sync_branch_need_sync(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=[
            None, 'main', 'master', 1, 'ok'
        ]
    )

    branch = 'main'
    check_and_sync_branch(branch)
    
    assert fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{branch}"]),
        call(["git", "rev-list", "--count", f"{branch}..origin/{branch}"]),
        call(["git", "pull", "--rebase", "origin", branch], loading_msg="Pulling changes from remote...", ok_text="Synced with remote.")
    ]

def test_check_and_sync_branch_no_remote(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=GitCommandError(['git', 'fetch'], stderr='error', returncode=1)
    )

    fake_warning = mocker.patch('pygitgo.commands.git_remote.warning')

    check_and_sync_branch('main')

    fake_warning.assert_called_with("Could not fetch from remote. Proceeding with push...")

    fake_run.assert_called_with(
        ["git", "fetch", "origin"], 
        loading_msg="Checking if branch is up to date..."
    )

def test_check_and_sync_branch_remote_not_exist(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_remote.run_command',
        side_effect=[None, GitCommandError(['git', 'rev-parse'], stderr='error', returncode=1)]
    )

    fake_warning = mocker.patch('pygitgo.commands.git_remote.warning')

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

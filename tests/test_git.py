from pygitgo.commands.git_operations import (
    git_new_branch, git_commit, get_current_branch,
    git_init, create_main_branch, add_remote_origin,
    confirm_remote_link, is_branch_exist, git_push,
    handle_rebase, check_and_sync_branch
)
from pygitgo.commands.state import (
    delete_state, save_state, load_state, validate_state_id, 
    all_save_state
)
from unittest.mock import call
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

    fake_success.assert_called_once_with("Branch is up to date or ahead of remote.")
    
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

    fake_success.assert_called_once_with("Successfully synced with remote!")
    
    fake_run.call_args_list == [
        call(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date..."),
        call(["git", "rev-parse", branch]),
        call(["git", "rev-parse", f"origin/{remote_branch}"]),
        call(["git", "rev-list", "--count", f"{branch}..origin/{remote_branch}"]),
        call(["git", "pull", "--rebase", "origin", remote_branch], loading_msg="Pulling changes from remote...")
    ]

def test_check_and_sync_branch_no_remote(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=subprocess.CalledProcessError(1, 'git')
    )

    fake_warning = mocker.patch('pygitgo.commands.git_operations.warning')

    check_and_sync_branch('main')

    fake_warning.assert_called_with("Could not fetch from remote. Proceeding with push...")

    fake_run.assert_called_with(
        ["git", "fetch", "origin"], 
        loading_msg="Checking if branch is up to date..."
    )

def test_check_and_sync_branch_remote_not_exist(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_operations.run_command',
        side_effect=[None,subprocess.CalledProcessError(1, 'git')]
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

@pytest.mark.parametrize('state_id',[
    '1', '3', '11', '00002', '7.0'
])
def test_validate_state_id(state_id, mocker):
    fake_error = mocker.patch('pygitgo.commands.state.error')

    save_states = [1] * 12
    result = validate_state_id(state_id, save_states)
    assert result == True

    fake_error.assert_not_called()

@pytest.mark.parametrize('state_id',[
    '-1', '-3', '-11', '-00002', '-7.0'
])
def test_validate_state_id_negative(state_id, mocker):

    save_states = [1] * 12
    fake_error = mocker.patch('pygitgo.commands.state.error')

    result = validate_state_id(state_id, save_states)
    assert result == False

    fake_error.assert_called_with("\nState ID cannot be '0' or negative. Please enter a valid state ID.\n")

@pytest.mark.parametrize('state_id',[
    '4', '10', '15', '0000020', '00007.00000'
])
def test_validate_state_id_out_scope(state_id, mocker):

    save_states = [1] * 3
    fake_error = mocker.patch('pygitgo.commands.state.error')

    result = validate_state_id(state_id, save_states)
    assert result == False

    fake_error.assert_called_with("\nState ID out of range. Please enter a valid state ID.\n")


def test_all_save_state_no_output(mocker):
    fake_run = mocker.patch("pygitgo.commands.state.run_command", return_value="")
    fake_info = mocker.patch("pygitgo.commands.state.info")

    with pytest.raises(SystemExit) as exc_info:
        all_save_state()

    assert exc_info.value.code == 0
    fake_info.assert_called_once_with("\nNo saved states found.\n")
    fake_run.assert_called_once_with([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])

def test_all_save_state_with_output(mocker):
    output = "stash@{0}||2023-10-27 10:00:00||Test stash\nstash@{1}||2023-10-27 10:05:00||Another stash"
    fake_run = mocker.patch("pygitgo.commands.state.run_command", return_value=output)

    result = all_save_state()

    assert len(result) == 2
    assert result[0] == {
        "id": 1,
        "ref": "stash@{0}",
        "date": "2023-10-27 10:00:00",
        "message": "Test stash"
    }
    assert result[1] == {
        "id": 2,
        "ref": "stash@{1}",
        "date": "2023-10-27 10:05:00",
        "message": "Another stash"
    }
    fake_run.assert_called_once_with([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])

def test_all_save_state_malformed_line(mocker):
    output = "malformed_line_here\nstash@{1}||2023-10-27 10:05:00||Another stash"
    fake_run = mocker.patch("pygitgo.commands.state.run_command", return_value=output)
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    result = all_save_state()

    assert len(result) == 1
    assert result[0] == {
        "id": 2,
        "ref": "stash@{1}",
        "date": "2023-10-27 10:05:00",
        "message": "Another stash"
    }
    fake_warning.assert_called_once_with("Skipping malformed line: malformed_line_here")
    fake_run.assert_called_once_with([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ])

def test_load_state_too_many_args(mocker):
    fake_error = mocker.patch("pygitgo.commands.state.error")

    with pytest.raises(SystemExit) as exc_info:
        load_state(["load", "1", "extra"])

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nToo many arguments for load operation!\n")

def test_load_state_help(mocker):
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[])
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    with pytest.raises(SystemExit) as exc_info:
        load_state(["load", "-h"])

    assert exc_info.value.code == 0
    fake_warning.assert_called_once_with("\nUsage:\n")

def test_load_state_specific_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=True)
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    load_state(["load", "1"])

    fake_run.assert_called_once_with(["git", "stash", "apply", "0"])
    fake_success.assert_called_once_with("\nState 'msg' loaded successfully.\n")

def test_load_state_invalid_id(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=False)

    with pytest.raises(SystemExit) as exc_info:
        load_state(["load", "100"])

    assert exc_info.value.code == 1

def test_load_state_invalid_argument(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    fake_error = mocker.patch("pygitgo.commands.state.error")

    with pytest.raises(SystemExit) as exc_info:
        load_state(["load", "invalid_arg"])

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nInvalid argument 'invalid_arg' for load operation. Expected a state ID.\n")

def test_load_state_no_args(mocker):
    save_states = [{"id": 1, "ref": "stash@{0}", "date": "date", "message": "msg"},
                   {"id": 2, "ref": "stash@{1}", "date": "date2", "message": "msg2"}]
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=save_states)
    mocker.patch("pygitgo.commands.state.ask_state_id", return_value="2")
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    load_state(["load"])

    fake_run.assert_called_once_with(["git", "stash", "apply", "1"])
    fake_success.assert_called_once_with("\nState 'msg2' loaded successfully.\n")

def test_save_state_too_many_args(mocker):
    fake_error = mocker.patch("pygitgo.commands.state.error")

    with pytest.raises(SystemExit) as exc_info:
        save_state(["save", "name", "extra"])

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nToo many arguments for save operation!\n")

def test_save_state_help(mocker):
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    with pytest.raises(SystemExit) as exc_info:
        save_state(["save", "-h"])

    assert exc_info.value.code == 0
    fake_warning.assert_called_once_with("\nUsage:\n")

def test_save_state_no_args(mocker):
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    save_state(["save"])

    fake_run.assert_called_once_with(["git", "stash", "push", "-m", "Auto-Save"])
    fake_success.assert_called_once_with("\nState 'Auto-Save' saved successfully.\n")

def test_save_state_with_name(mocker):
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    save_state(["save", "My-State"])

    fake_run.assert_called_once_with(["git", "stash", "push", "-m", "My-State"])
    fake_success.assert_called_once_with("\nState 'My-State' saved successfully.\n")

def test_delete_state_too_many_args(mocker):
    fake_error = mocker.patch("pygitgo.commands.state.error")

    with pytest.raises(SystemExit) as exc_info:
        delete_state(["delete", "1", "extra"])

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nToo many arguments for delete operation!\n")

def test_delete_state_help(mocker):
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    with pytest.raises(SystemExit) as exc_info:
        delete_state(["delete", "-h"])

    assert exc_info.value.code == 0
    fake_warning.assert_called_once_with("\nUsage:\n")

def test_delete_state_all_confirm(mocker):
    mocker.patch("builtins.input", return_value="y")
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    with pytest.raises(SystemExit) as exc_info:
        delete_state(["delete", "-a"])

    assert exc_info.value.code == 0
    fake_run.assert_called_once_with(["git", "stash", "clear"])
    fake_success.assert_called_once_with("\nAll saved states deleted successfully.\n")

def test_delete_state_all_cancel(mocker):
    mocker.patch("builtins.input", return_value="n")
    fake_warning = mocker.patch("pygitgo.commands.state.warning")

    with pytest.raises(SystemExit) as exc_info:
        delete_state(["delete", "-a"])

    assert exc_info.value.code == 0
    fake_warning.assert_called_once_with("\nDelete operation cancelled by user.\n")

def test_delete_state_invalid_id(mocker):
    fake_error = mocker.patch("pygitgo.commands.state.error")
    
    with pytest.raises(SystemExit) as exc_info:
        delete_state(["delete", "abc"])

    assert exc_info.value.code == 1
    fake_error.assert_called_once_with("\nInvalid input. Please enter a valid state ID.\n")

def test_delete_state_specific_id(mocker):
    mocker.patch("pygitgo.commands.state.validate_state_id", return_value=True)
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[])
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state(["delete", "1"])

    fake_run.assert_called_once_with(["git", "stash", "drop", "0"])
    fake_success.assert_called_once_with("\nState with ID '1' deleted successfully.\n")

def test_delete_state_no_args(mocker):
    mocker.patch("pygitgo.commands.state.all_save_state", return_value=[])
    mocker.patch("pygitgo.commands.state.ask_state_id", return_value="2")
    fake_run = mocker.patch("pygitgo.commands.state.run_command")
    fake_success = mocker.patch("pygitgo.commands.state.success")

    delete_state(["delete"])

    fake_run.assert_called_once_with(["git", "stash", "drop", "1"])
    fake_success.assert_called_once_with("\nState with ID '2' deleted successfully.\n")

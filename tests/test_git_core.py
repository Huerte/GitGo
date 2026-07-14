from pygitgo.commands.git_core import (
    git_commit, git_init, git_push
)


def test_git_commit(mocker):
    mocker.patch("pygitgo.commands.git_core._get_signing_flags", return_value=[])
    fake_sanitize = mocker.patch("pygitgo.commands.git_core.sanitize_signing_config")
    fake_run = mocker.patch("pygitgo.commands.git_core.run_command")
    
    result = git_commit("Testing the commit feature")
    assert result == True
    fake_sanitize.assert_called_once()

    fake_run.assert_any_call(
        ['git', 'commit', '-S', '-m', 'Testing the commit feature'],
        loading_msg="Committing changes...",
        ok_text="Changes committed."
    )

def test_git_init_already_initialized(mocker):
    mocker.patch('os.path.isdir', return_value=True)
    fake_warning = mocker.patch('pygitgo.commands.git_core.warning')
    fake_run = mocker.patch('pygitgo.commands.git_core.run_command')

    result = git_init()

    assert result == False
    fake_warning.assert_called_once() 
    fake_run.assert_not_called()

def test_git_init_success(mocker):
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('pygitgo.commands.git_core.get_default_branch', return_value='main')
    fake_run = mocker.patch('pygitgo.commands.git_core.run_command', return_value='ok')

    result = git_init()

    assert result == True
    fake_run.assert_called_once_with(
        ["git", "init", "-b", 'main'], 
        loading_msg="Initializing git repository...",
        ok_text="Git repository initialized."
    )

def test_git_init_fallback(mocker):
    from pygitgo.exceptions import GitCommandError
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('pygitgo.commands.git_core.get_default_branch', return_value='main')
    
    fake_run = mocker.patch(
        'pygitgo.commands.git_core.run_command', 
        side_effect=[
            GitCommandError(["git", "init", "-b", "main"]),
            "init_success",
            "checkout_success"
        ]
    )

    result = git_init()

    assert result == True
    assert fake_run.call_count == 3

def test_git_push_already_ssh(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_core.run_command',
        side_effect=[
            'git@github.com:user/repo.git\n', None
        ]
    )
    mocker.patch('pygitgo.commands.git_core.is_ssh_url', return_value=True)

    branch = 'main'
    git_push(branch)

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'...",
        ok_text=f"Pushed to remote branch '{branch}'.",
        err_text="Push failed: verify your remote URL and SSH key, then try again."
    )

def test_git_push_no_remote(mocker):
    from pygitgo.exceptions import GitCommandError
    fake_run = mocker.patch(
        'pygitgo.commands.git_core.run_command', 
        side_effect=[
            GitCommandError(["git", "remote", "get-url"]),
            "pushed"
        ]
    )

    branch = 'main'
    git_push(branch)

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'...",
        ok_text=f"Pushed to remote branch '{branch}'.",
        err_text="Push failed: verify your remote URL and SSH key, then try again."
    )

def test_git_push_https_no_connection(mocker):
    fake_run = mocker.patch(
        'pygitgo.commands.git_core.run_command',
        side_effect=[
            'https://github.com/user/repo.git\n',
            None
        ]
    )

    mocker.patch('pygitgo.commands.git_core.is_ssh_url', return_value=False)
    mocker.patch('pygitgo.commands.git_core.check_connection', return_value=False)
    
    branch = 'main'
    git_push(branch)

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'...",
        ok_text=f"Pushed to remote branch '{branch}'.",
        err_text="Push failed: verify your remote URL and SSH key, then try again."
    )

def test_git_push_convert_https_to_ssh(mocker):
    url = 'https://github.com/user/repo.git\n'
    fake_run = mocker.patch(
        'pygitgo.commands.git_core.run_command',
        side_effect=[
            url,
            None, None
        ]
    )

    mocker.patch('pygitgo.commands.git_core.is_ssh_url', return_value=False)
    mocker.patch('pygitgo.commands.git_core.check_connection', return_value=True)
    mocker.patch('pygitgo.commands.git_core.convert_https_to_ssh', return_value=url)

    branch = 'main'
    git_push(branch)

    fake_run.assert_any_call(
        ["git", "remote", "set-url", "origin", url], 
        loading_msg="Converting remote from HTTPS to SSH for secure push...",
        ok_text=f"Remote updated to: {url}"
    )

    fake_run.assert_called_with(
        ["git", "push", "-u", "origin", branch], 
        loading_msg=f"Pushing to remote branch '{branch}'...",
        ok_text=f"Pushed to remote branch '{branch}'.",
        err_text="Push failed: verify your remote URL and SSH key, then try again."
    )

def test_git_commit_skip_staging_does_not_run_git_add(mocker):
    mocker.patch("pygitgo.commands.git_core._get_signing_flags", return_value=[])
    mocker.patch("pygitgo.commands.git_core.sanitize_signing_config")
    fake_run = mocker.patch("pygitgo.commands.git_core.run_command")
    
    fake_run.side_effect = ["M file.py", None]
    git_commit("my message", skip_staging=True)

    for call in fake_run.call_args_list:
        args = call[0][0]
        assert args[:2] != ["git", "add"], "git add should not run when skip_staging=True"

def test_git_commit_default_runs_git_add(mocker):
    mocker.patch("pygitgo.commands.git_core._get_signing_flags", return_value=[])
    mocker.patch("pygitgo.commands.git_core.sanitize_signing_config")
    fake_run = mocker.patch("pygitgo.commands.git_core.run_command")
    fake_run.side_effect = ["M file.py", None, None]
    git_commit("my message")
    add_call = fake_run.call_args_list[1][0][0]
    assert add_call == ["git", "add", "."]


def test_abort_pull_conflict_active_rebase(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pygitgo.utils.cli_io.confirm", return_value=True)
    fake_run = mocker.patch("pygitgo.utils.executor.run_command")
    
    from pygitgo.commands.git_core import abort_pull_conflict
    result = abort_pull_conflict()
    
    assert result is True
    fake_run.assert_called_once_with(["git", "rebase", "--abort"], loading_msg="Aborting sync...", ok_text="Sync aborted. Branch is back to how it was before the conflict.")


def test_abort_pull_conflict_no_rebase(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pygitgo.utils.cli_io.confirm", return_value=True)
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main")
    fake_run = mocker.patch("pygitgo.utils.executor.run_command", side_effect=["", "", "0"])
    
    from pygitgo.commands.git_core import abort_pull_conflict
    result = abort_pull_conflict()
    
    assert result is True
    fake_run.assert_any_call(["git", "reset", "--hard", "ORIG_HEAD"], loading_msg="Reverting to pre-pull state...", ok_text="Branch reset to its state before the last pull.")

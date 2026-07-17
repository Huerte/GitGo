from pygitgo.exceptions import GitGoError, GitCommandError
from pygitgo.commands.git_core import (
    git_commit,
    git_init,
    git_push,
    ensure_inside_git_repository,
    is_git_repository,
    has_local_changes,
    is_rebase_in_progress,
    has_any_commits,
    get_recent_commits,
    _get_signing_flags,
    abort_pull_conflict
)
from pathlib import Path
import pytest

def test_git_commit(mocker):
    mocker.patch("pygitgo.commands.git_core._get_signing_flags", return_value=[])
    fake_sanitize = mocker.patch("pygitgo.commands.git_core.sanitize_signing_config")
    fake_run = mocker.patch("pygitgo.commands.git_core.run_command")
    fake_run.side_effect = ["M file.py", None, None]
    
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
        assert args[:2] != ["git", "add"]

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
    
    result = abort_pull_conflict()
    
    assert result is True
    fake_run.assert_called_once_with(["git", "rebase", "--abort"], loading_msg="Aborting sync...", ok_text="Sync aborted. Branch is back to how it was before the conflict.")

def test_abort_pull_conflict_no_rebase(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pygitgo.utils.cli_io.confirm", return_value=True)
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main")
    fake_run = mocker.patch("pygitgo.utils.executor.run_command", side_effect=["", "", "0"])
    
    result = abort_pull_conflict()
    
    assert result is True
    fake_run.assert_any_call(["git", "reset", "--hard", "ORIG_HEAD"], loading_msg="Reverting to pre-pull state...", ok_text="Branch reset to its state before the last pull.")

def test_ensure_inside_git_repository(mocker):
    mocker.patch("pygitgo.commands.git_core.is_git_repository", return_value=True)
    ensure_inside_git_repository()

    mocker.patch("pygitgo.commands.git_core.is_git_repository", return_value=False)
    with pytest.raises(GitGoError):
        ensure_inside_git_repository()

def test_is_git_repository(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", return_value="true")
    assert is_git_repository() is True

    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=GitCommandError(["cmd"]))
    assert is_git_repository() is False

def test_has_local_changes(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", return_value="M test.py")
    assert has_local_changes() is True

    mocker.patch("pygitgo.commands.git_core.run_command", return_value="")
    assert has_local_changes() is False

    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=GitCommandError(["cmd"]))
    assert has_local_changes() is False

def test_is_rebase_in_progress(mocker):
    def mock_exists(self):
        return "rebase-merge" in str(self)
    mocker.patch.object(Path, "exists", mock_exists)
    assert is_rebase_in_progress() is True

def test_has_any_commits(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", return_value="abcdef")
    assert has_any_commits() is True

    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=GitCommandError(["cmd"]))
    assert has_any_commits() is False

def test_get_recent_commits(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", return_value="abc||author||date||msg\ninvalidline\ndef||author2||date2||msg2")
    commits = get_recent_commits(number=2, branch="main")
    assert len(commits) == 2
    assert commits[0]["hash"] == "abc"
    assert commits[1]["hash"] == "def"

    mocker.patch("pygitgo.commands.git_core.run_command", return_value="")
    assert get_recent_commits() == []

    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=GitCommandError(["cmd"], stderr="err"))
    with pytest.raises(GitGoError):
        get_recent_commits()

def test_get_signing_flags(mocker):
    mock_path = mocker.MagicMock()
    mock_path.exists.return_value = True
    mocker.patch("pygitgo.commands.git_core.get_ssh_key_path", return_value=mock_path)
    flags = _get_signing_flags()
    assert len(flags) > 0

    mock_path.exists.return_value = False
    assert _get_signing_flags() == []

def test_git_commit_no_changes(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", return_value="")
    assert git_commit("msg") is False

def test_git_commit_status_error(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=GitCommandError(["cmd"], stderr="not a git repository"))
    with pytest.raises(GitGoError) as ex:
        git_commit("msg")
    assert "Not inside a git repository" in str(ex.value)

    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=GitCommandError(["cmd"], stderr="other error"))
    with pytest.raises(GitGoError) as ex:
        git_commit("msg")
    assert "Could not check repository status" in str(ex.value)

def test_git_push_non_fast_forward(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=[
        "git@github.com:user/repo.git",
        GitCommandError(["push"], stderr="rejected (non-fast-forward)")
    ])
    mocker.patch("pygitgo.commands.git_core.is_ssh_url", return_value=True)
    with pytest.raises(GitGoError) as ex:
        git_push("main")
    assert "Push rejected" in str(ex.value)

def test_git_push_repository_not_found(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=[
        "git@github.com:user/repo.git",
        GitCommandError(["push"], stderr="repository not found")
    ])
    mocker.patch("pygitgo.commands.git_core.is_ssh_url", return_value=True)
    with pytest.raises(GitGoError) as ex:
        git_push("main")
    assert "remote repository not found" in str(ex.value)

def test_git_push_permission_denied(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=[
        "git@github.com:user/repo.git",
        GitCommandError(["push"], stderr="permission denied")
    ])
    mocker.patch("pygitgo.commands.git_core.is_ssh_url", return_value=True)
    with pytest.raises(GitGoError) as ex:
        git_push("main")
    assert "permission denied" in str(ex.value)

def test_git_push_other_error(mocker):
    mocker.patch("pygitgo.commands.git_core.run_command", side_effect=[
        "git@github.com:user/repo.git",
        GitCommandError(["push"], stderr="unknown failure")
    ])
    mocker.patch("pygitgo.commands.git_core.is_ssh_url", return_value=True)
    with pytest.raises(GitGoError) as ex:
        git_push("main")
    assert "Push failed: unknown failure" in str(ex.value)

def test_abort_pull_conflict_active_rebase_decline(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pygitgo.utils.cli_io.confirm", return_value=False)
    assert abort_pull_conflict() is False

def test_abort_pull_conflict_active_rebase_error(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pygitgo.utils.cli_io.confirm", return_value=True)
    mocker.patch("pygitgo.utils.executor.run_command", side_effect=GitCommandError(["cmd"], stderr="abort error"))
    with pytest.raises(GitGoError):
        abort_pull_conflict()

def test_abort_pull_conflict_no_orig_head(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pygitgo.utils.executor.run_command", side_effect=GitCommandError(["cmd"]))
    with pytest.raises(GitGoError) as ex:
        abort_pull_conflict()
    assert "No pull to undo" in str(ex.value)

def test_abort_pull_conflict_branch_error(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pygitgo.utils.executor.run_command", return_value="")
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", side_effect=GitCommandError(["cmd"]))
    with pytest.raises(GitGoError):
        abort_pull_conflict()

def test_abort_pull_conflict_reset_error(mocker):
    mocker.patch("pathlib.Path.exists", return_value=False)
    mocker.patch("pygitgo.commands.git_branch.get_current_branch", return_value="main")
    mocker.patch("pygitgo.utils.cli_io.confirm", return_value=True)
    mocker.patch("pygitgo.utils.executor.run_command", side_effect=[
        "",
        GitCommandError(["cmd"], stderr="reset error")
    ])
    with pytest.raises(GitGoError):
        abort_pull_conflict()
